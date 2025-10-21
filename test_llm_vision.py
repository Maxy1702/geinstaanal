"""
Test LLM Vision Capabilities
"""
import logging
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config_loader import Config
from image_handler import ImageCache
from llm_client import LLMClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    logger.info("="*60)
    logger.info("Test 1: LM Studio Connection")
    logger.info("="*60)
    
    config = Config()
    client = LLMClient(
        api_endpoint=config.get('llm', 'api_endpoint'),
        model_name=config.get('llm', 'model_name'),
        timeout=120,
        temperature=0.3
    )
    
    logger.info(f"Endpoint: {client.api_endpoint}")
    logger.info(f"Model: {client.model_name}")
    
    if client.test_connection():
        logger.info("✅ Connected!\n")
        return client
    else:
        logger.error("❌ Connection failed!")
        return None

def test_vision(client):
    logger.info("="*60)
    logger.info("Test 2: Vision Analysis")
    logger.info("="*60)
    
    config = Config()
    cache_dir = Path(config.get('data', 'image_cache_dir'))
    images = list(cache_dir.glob('*.jpg'))
    
    if not images:
        logger.error("❌ No images found!")
        return False
    
    test_img = images[0]
    logger.info(f"Testing with: {test_img.name}")
    
    system_prompt = "Describe the image in JSON format."
    user_prompt = """Describe this image.

Return JSON:
{
  "description": "what you see",
  "objects": ["list of objects"]
}"""
    
    logger.info("\n🤖 Analyzing...")
    
    result = client.analyze_post(
        post={'id': 'test'},
        image_paths=[test_img],
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )
    
    if result:
        logger.info("\n✅ Success!")
        logger.info(json.dumps(result, indent=2))
        return True
    else:
        logger.error("\n❌ Failed!")
        return False

if __name__ == '__main__':
    print("\n=== LLM Vision Test ===\n")
    client = test_connection()
    if client:
        input("Press Enter to test vision...")
        test_vision(client)
    print("\n=== Test Complete ===\n")
