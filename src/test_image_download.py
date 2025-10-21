"""
Test Image Downloader
Download images for sample posts to verify everything works
"""
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config_loader import Config
from json_parser import parse_instagram_data
from image_handler import ImageDownloader, ImageCache, download_images_batch

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_single_post():
    """Test downloading images for a single post"""
    logger.info("="*80)
    logger.info("Test 1: Single Post Download")
    logger.info("="*80)
    
    config = Config()
    
    # Parse sample posts
    posts, _ = parse_instagram_data(
        json_path=config.input_file,
        mode='sample',
        sample_size=5
    )
    
    # Get first post with images
    test_post = None
    for post in posts:
        if post['media']['image_count'] > 0:
            test_post = post
            break
    
    if not test_post:
        logger.error("No posts with images found!")
        return
    
    logger.info(f"\nTest Post:")
    logger.info(f"  ID: {test_post['id']}")
    logger.info(f"  Type: {test_post['type']}")
    logger.info(f"  Owner: @{test_post['owner']['username']}")
    logger.info(f"  Images: {test_post['media']['image_count']}")
    
    # Download images
    downloader = ImageDownloader(config.get('data', 'image_cache_dir'))
    
    logger.info(f"\n📥 Downloading images...")
    results = downloader.download_post_images(
        post_id=test_post['id'],
        image_urls=test_post['media']['images'],
        max_images=config.get('images', 'max_images_per_post', default=10)
    )
    
    # Show results
    logger.info(f"\n📊 Download Results:")
    for r in results:
        status = "✅ Cached" if r.get('cached') else "✅ Downloaded" if r['success'] else "❌ Failed"
        logger.info(f"  Image {r['index']+1}: {status}")
        if r['success']:
            logger.info(f"    Path: {r['local_path']}")
        else:
            logger.info(f"    Error: {r.get('error', 'Unknown')}")
    
    # Stats
    stats = downloader.get_stats()
    logger.info(f"\n📈 Statistics:")
    logger.info(f"  Downloaded: {stats['downloaded']}")
    logger.info(f"  Cached: {stats['cached']}")
    logger.info(f"  Failed: {stats['failed']}")
    
    downloader.close()
    logger.info("\n✅ Single post test complete!")


def test_batch_download():
    """Test downloading images for multiple posts"""
    logger.info("\n" + "="*80)
    logger.info("Test 2: Batch Download (10 posts)")
    logger.info("="*80)
    
    config = Config()
    
    # Parse 10 sample posts
    posts, _ = parse_instagram_data(
        json_path=config.input_file,
        mode='sample',
        sample_size=10
    )
    
    logger.info(f"\n📦 Processing {len(posts)} posts...")
    
    # Batch download
    results = download_images_batch(
        posts=posts,
        cache_dir=Path(config.get('data', 'image_cache_dir')),
        max_images_per_post=config.get('images', 'max_images_per_post', default=10),
        show_progress=True
    )
    
    # Verify cache
    cache = ImageCache(config.get('data', 'image_cache_dir'))
    cache_stats = cache.get_cache_stats()
    
    logger.info(f"\n💾 Cache Statistics:")
    logger.info(f"  Total images: {cache_stats['total_images']}")
    logger.info(f"  Total size: {cache_stats['total_size_mb']} MB")
    logger.info(f"  Cache dir: {cache_stats['cache_dir']}")
    
    # Show sample cached post
    logger.info(f"\n🔍 Checking first post cache...")
    first_post_id = posts[0]['id']
    cached_images = cache.get_post_images(first_post_id)
    logger.info(f"  Post {first_post_id}:")
    logger.info(f"  Cached images: {len(cached_images)}")
    for img_path in cached_images:
        logger.info(f"    - {img_path.name}")
    
    logger.info("\n✅ Batch download test complete!")


def test_cache_lookup():
    """Test cache lookup utilities"""
    logger.info("\n" + "="*80)
    logger.info("Test 3: Cache Lookup")
    logger.info("="*80)
    
    config = Config()
    cache = ImageCache(config.get('data', 'image_cache_dir'))
    
    # Parse one post
    posts, _ = parse_instagram_data(
        json_path=config.input_file,
        mode='sample',
        sample_size=1
    )
    
    post = posts[0]
    post_id = post['id']
    
    logger.info(f"\nLooking up post: {post_id}")
    
    # Check if cached
    is_cached = cache.is_post_cached(post_id)
    logger.info(f"  Is cached: {is_cached}")
    
    if is_cached:
        images = cache.get_post_images(post_id)
        logger.info(f"  Cached images: {len(images)}")
        for img in images:
            size_kb = img.stat().st_size / 1024
            logger.info(f"    - {img.name} ({size_kb:.1f} KB)")
    
    logger.info("\n✅ Cache lookup test complete!")


def main():
    """Run all tests"""
    try:
        # Test 1: Single post download
        test_single_post()
        
        # Test 2: Batch download
        test_batch_download()
        
        # Test 3: Cache lookup
        test_cache_lookup()
        
        logger.info("\n" + "="*80)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()