"""
Image Handler - Download and cache Instagram images
"""
import requests
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)


class ImageDownloader:
    """Download and cache Instagram images"""
    
    def __init__(self, cache_dir: Path, timeout: int = 30, max_retries: int = 3):
        """
        Initialize image downloader
        
        Args:
            cache_dir: Directory to cache downloaded images
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed downloads
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Track statistics
        self.stats = {
            'downloaded': 0,
            'cached': 0,
            'failed': 0,
            'total_attempts': 0
        }
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def download_post_images(
        self, 
        post_id: str, 
        image_urls: List[str],
        max_images: int = 10
    ) -> List[Dict[str, any]]:
        """
        Download all images for a post
        
        Args:
            post_id: Instagram post ID
            image_urls: List of image URLs to download
            max_images: Maximum number of images to download per post
        
        Returns:
            List of dicts with 'url', 'local_path', 'success', 'error' keys
        """
        results = []
        
        # Limit number of images
        urls_to_download = image_urls[:max_images]
        
        logger.debug(f"Processing {len(urls_to_download)} images for post {post_id}")
        
        for idx, url in enumerate(urls_to_download):
            self.stats['total_attempts'] += 1
            
            # Generate filename: postid_index_hash.jpg
            filename = self._generate_filename(post_id, url, idx)
            local_path = self.cache_dir / filename
            
            # Check if already cached
            if local_path.exists():
                logger.debug(f"  Image {idx+1}: Cached ✓")
                self.stats['cached'] += 1
                results.append({
                    'url': url,
                    'local_path': local_path,
                    'success': True,
                    'cached': True,
                    'index': idx
                })
                continue
            
            # Download image
            success, error = self._download_image(url, local_path)
            
            if success:
                logger.debug(f"  Image {idx+1}: Downloaded ✓")
                self.stats['downloaded'] += 1
                results.append({
                    'url': url,
                    'local_path': local_path,
                    'success': True,
                    'cached': False,
                    'index': idx
                })
            else:
                logger.warning(f"  Image {idx+1}: Failed - {error}")
                self.stats['failed'] += 1
                results.append({
                    'url': url,
                    'local_path': None,
                    'success': False,
                    'cached': False,
                    'error': error,
                    'index': idx
                })
        
        return results
    
    def _download_image(self, url: str, save_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Download single image with retry logic
        
        Args:
            url: Image URL
            save_path: Where to save the image
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, stream=True)
                
                if response.status_code == 200:
                    # Save image
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Verify file was written
                    if save_path.exists() and save_path.stat().st_size > 0:
                        return True, None
                    else:
                        return False, "File empty after download"
                
                elif response.status_code == 404:
                    return False, f"Image not found (404)"
                
                else:
                    error_msg = f"HTTP {response.status_code}"
                    if attempt < self.max_retries - 1:
                        logger.debug(f"    Retry {attempt+1}/{self.max_retries}: {error_msg}")
                        time.sleep(1)  # Brief pause before retry
                        continue
                    return False, error_msg
            
            except requests.exceptions.Timeout:
                error_msg = "Timeout"
                if attempt < self.max_retries - 1:
                    logger.debug(f"    Retry {attempt+1}/{self.max_retries}: {error_msg}")
                    time.sleep(1)
                    continue
                return False, error_msg
            
            except requests.exceptions.ConnectionError:
                error_msg = "Connection error"
                if attempt < self.max_retries - 1:
                    logger.debug(f"    Retry {attempt+1}/{self.max_retries}: {error_msg}")
                    time.sleep(2)
                    continue
                return False, error_msg
            
            except Exception as e:
                return False, f"Unexpected error: {str(e)}"
        
        return False, "Max retries exceeded"
    
    def _generate_filename(self, post_id: str, url: str, index: int) -> str:
        """
        Generate unique filename for cached image
        
        Format: {post_id}_{index}_{url_hash}.jpg
        
        Args:
            post_id: Instagram post ID
            url: Image URL
            index: Image index in post (0, 1, 2...)
        
        Returns:
            Filename string
        """
        # Hash URL to create short unique identifier (first 8 chars)
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Extract extension from URL (default to .jpg)
        parsed = urlparse(url)
        path = parsed.path
        ext = Path(path).suffix if Path(path).suffix else '.jpg'
        
        return f"{post_id}_{index}_{url_hash}{ext}"
    
    def get_stats(self) -> Dict[str, int]:
        """Get download statistics"""
        return self.stats.copy()
    
    def get_cache_size(self) -> int:
        """Get number of cached images"""
        return len(list(self.cache_dir.glob('*')))
    
    def clear_cache(self):
        """Clear all cached images (use with caution!)"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache cleared: {self.cache_dir}")
    
    def close(self):
        """Close session"""
        self.session.close()


class ImageCache:
    """Manage image cache and provide lookup utilities"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
    
    def get_post_images(self, post_id: str) -> List[Path]:
        """
        Get all cached images for a post
        
        Args:
            post_id: Instagram post ID
        
        Returns:
            List of paths to cached images, sorted by index
        """
        pattern = f"{post_id}_*"
        images = list(self.cache_dir.glob(pattern))
        
        # Sort by index (extracted from filename)
        def get_index(path):
            try:
                # Filename format: postid_INDEX_hash.jpg
                return int(path.stem.split('_')[1])
            except:
                return 999
        
        return sorted(images, key=get_index)
    
    def is_post_cached(self, post_id: str) -> bool:
        """Check if post has any cached images"""
        pattern = f"{post_id}_*"
        return len(list(self.cache_dir.glob(pattern))) > 0
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics"""
        all_files = list(self.cache_dir.glob('*'))
        total_size = sum(f.stat().st_size for f in all_files)
        
        return {
            'total_images': len(all_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir)
        }


# Convenience function for batch processing
def download_images_batch(
    posts: List[Dict],
    cache_dir: Path,
    max_images_per_post: int = 10,
    show_progress: bool = True
) -> Dict[str, List[Dict]]:
    """
    Download images for multiple posts
    
    Args:
        posts: List of normalized post dicts
        cache_dir: Cache directory path
        max_images_per_post: Max images to download per post
        show_progress: Show progress bar
    
    Returns:
        Dict mapping post_id -> list of image results
    """
    downloader = ImageDownloader(cache_dir)
    results = {}
    
    try:
        if show_progress:
            from tqdm import tqdm
            posts_iter = tqdm(posts, desc="Downloading images", unit="post")
        else:
            posts_iter = posts
        
        for post in posts_iter:
            post_id = post['id']
            image_urls = post['media']['images']
            
            # Download images for this post
            image_results = downloader.download_post_images(
                post_id=post_id,
                image_urls=image_urls,
                max_images=max_images_per_post
            )
            
            results[post_id] = image_results
        
        # Log final stats
        stats = downloader.get_stats()
        logger.info(f"\nImage Download Summary:")
        logger.info(f"  Downloaded: {stats['downloaded']}")
        logger.info(f"  Cached: {stats['cached']}")
        logger.info(f"  Failed: {stats['failed']}")
        logger.info(f"  Total attempts: {stats['total_attempts']}")
        
    finally:
        downloader.close()
    
    return results