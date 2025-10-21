"""
LLM Client - Vision-enabled wrapper for LM Studio
Supports multimodal analysis (images + text)
"""
import requests
import json
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import io
import time

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for LM Studio API with vision support"""
    
    def __init__(
        self,
        api_endpoint: str,
        model_name: str,
        timeout: int = 120,
        max_retries: int = 3,
        temperature: float = 0.3
    ):
        """
        Initialize LLM client
        
        Args:
            api_endpoint: LM Studio API endpoint (e.g., http://127.0.0.1:512/v1)
            model_name: Model identifier
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            temperature: Sampling temperature (0.0-1.0)
        """
        self.api_endpoint = api_endpoint.rstrip('/')
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'retry_count': 0
        }
    
    def encode_image(self, image_path: Path, max_size: int = 896) -> str:
        """
        Encode image to base64 data URL
        
        Gemma 3 normalizes images to 896x896, so we resize before sending
        to save bandwidth.
        
        Args:
            image_path: Path to image file
            max_size: Maximum dimension (Gemma 3 uses 896x896)
        
        Returns:
            Base64 data URL string
        """
        try:
            # Open and resize image
            img = Image.open(image_path)
            
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Resize maintaining aspect ratio
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            img_bytes = buffer.getvalue()
            
            # Encode to base64
            b64_string = base64.b64encode(img_bytes).decode('utf-8')
            
            return f"data:image/jpeg;base64,{b64_string}"
            
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            raise
    
    def analyze_post(
        self,
        post: Dict[str, Any],
        image_paths: List[Path],
        system_prompt: str,
        user_prompt: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze Instagram post with images using vision model
        
        Args:
            post: Normalized post dictionary
            image_paths: List of paths to downloaded images
            system_prompt: System instructions
            user_prompt: User query with post content
        
        Returns:
            Parsed JSON response or None if failed
        """
        self.stats['total_requests'] += 1
        
        for attempt in range(self.max_retries):
            try:
                # Build message with images
                content = []
                
                # Add images first
                for img_path in image_paths[:4]:  # Limit to 4 images
                    if img_path.exists():
                        try:
                            img_data_url = self.encode_image(img_path)
                            content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": img_data_url
                                }
                            })
                        except Exception as e:
                            logger.warning(f"Failed to encode {img_path}: {e}")
                
                # Add text prompt
                content.append({
                    "type": "text",
                    "text": user_prompt
                })
                
                # Build request
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt + "\n\nIMPORTANT: You MUST respond with valid JSON only. No other text."
                        },
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    "temperature": self.temperature,
                    "max_tokens": 2000
                        # No response_format - rely on prompt                 
                    }
                
                # Make request
                response = requests.post(
                    f"{self.api_endpoint}/chat/completions",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract response text
                    if 'choices' in result and len(result['choices']) > 0:
                        response_text = result['choices'][0]['message']['content']
                        
                        # Track tokens
                        if 'usage' in result:
                            self.stats['total_tokens'] += result['usage'].get('total_tokens', 0)
                        
                        # Parse JSON response
                        try:
                            parsed = json.loads(response_text)
                            self.stats['successful_requests'] += 1
                            return parsed
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON response: {e}")
                            logger.debug(f"Raw response: {response_text}")
                            
                            # Try to extract JSON from response
                            import re
                            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                            if json_match:
                                try:
                                    parsed = json.loads(json_match.group())
                                    self.stats['successful_requests'] += 1
                                    return parsed
                                except:
                                    pass
                    
                    logger.error(f"Unexpected response format: {result}")
                    
                elif response.status_code == 503:
                    # Model loading or busy
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Model busy, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        self.stats['retry_count'] += 1
                        continue
                
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                    self.stats['retry_count'] += 1
                    continue
                    
            except Exception as e:
                logger.error(f"Error during analysis: {e}", exc_info=True)
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    self.stats['retry_count'] += 1
                    continue
        
        # All retries failed
        self.stats['failed_requests'] += 1
        return None
    
    def test_connection(self) -> bool:
        """
        Test connection to LM Studio server
        
        Returns:
            True if server is reachable and responding
        """
        try:
            response = requests.get(
                f"{self.api_endpoint}/models",
                timeout=5
            )
            
            if response.status_code == 200:
                models = response.json()
                logger.info(f"✅ Connected to LM Studio")
                logger.info(f"Available models: {models}")
                return True
            else:
                logger.error(f"Server responded with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Cannot connect to {self.api_endpoint}")
            logger.error("Make sure LM Studio server is running!")
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_requests'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            )
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'retry_count': 0
        }