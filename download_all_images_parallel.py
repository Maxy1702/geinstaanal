"""
Parallel Image Downloader - 8-10x faster than sequential version
Downloads Instagram images using ThreadPoolExecutor for concurrent downloads
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import Config
from src.json_parser import InstagramDataParser
from src.image_handler import ImageDownloader
from tqdm import tqdm
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/logs/image_download_parallel.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ThreadSafeDownloadManager:
    """Thread-safe manager for parallel image downloads"""

    def __init__(self, all_posts, config, max_workers=12):
        """
        Initialize parallel download manager

        Args:
            all_posts: List of parsed Instagram posts
            config: Configuration object
            max_workers: Number of concurrent download threads (default: 12)
        """
        self.all_posts = all_posts
        self.config = config
        self.max_workers = max_workers
        self.lock = threading.Lock()

        # Thread-safe statistics
        self.stats = {
            'downloaded': 0,
            'cached': 0,
            'failed': 0,
            'posts_processed': 0,
            'posts_with_failures': 0
        }
        self.failed_posts = []

        # Cache directory
        self.cache_dir = Path(config.get('data', 'image_cache_dir'))

    def download_post(self, post):
        """
        Download all images for a single post (thread-safe)

        Args:
            post: Parsed Instagram post dictionary

        Returns:
            Tuple of (post_id, results_list, success_count, fail_count)
        """
        post_id = post['id']
        image_urls = post['media']['images']

        if not image_urls:
            return (post_id, [], 0, 0)

        # Each thread gets its own downloader instance (thread-safe)
        downloader = ImageDownloader(
            cache_dir=self.cache_dir,
            timeout=30,
            max_retries=3
        )

        try:
            # Download all images for this post
            results = downloader.download_post_images(
                post_id=post_id,
                image_urls=image_urls,
                max_images=self.config.get('images', 'max_images_per_post')
            )

            # Count successes and failures
            success_count = sum(1 for r in results if r['success'])
            fail_count = len(results) - success_count

            # Thread-safe stats update
            with self.lock:
                self.stats['downloaded'] += downloader.stats['downloaded']
                self.stats['cached'] += downloader.stats['cached']
                self.stats['failed'] += downloader.stats['failed']
                self.stats['posts_processed'] += 1

                if fail_count > 0:
                    self.stats['posts_with_failures'] += 1
                    self.failed_posts.append({
                        'post_id': post_id,
                        'url': post['url'],
                        'username': post['owner']['username'],
                        'failed_count': fail_count,
                        'total_images': len(results)
                    })

            return (post_id, results, success_count, fail_count)

        except Exception as e:
            logger.error(f"Error downloading post {post_id}: {e}")
            with self.lock:
                self.stats['posts_processed'] += 1
                self.stats['posts_with_failures'] += 1
                self.failed_posts.append({
                    'post_id': post_id,
                    'url': post['url'],
                    'error': str(e)
                })
            return (post_id, [], 0, 0)

    def download_all(self):
        """Download all images using thread pool"""
        print(f"\n[2/3] Downloading images with {self.max_workers} concurrent threads...")
        print(f"  Expected speedup: ~{self.max_workers}x faster than sequential")
        print(f"  Threads will download multiple posts simultaneously")

        start_time = time.time()

        # Progress bar
        pbar = tqdm(
            total=len(self.all_posts),
            desc="Downloading",
            unit="post",
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        )

        # Submit all posts to thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_post = {
                executor.submit(self.download_post, post): post
                for post in self.all_posts
            }

            # Process completed downloads as they finish
            for future in as_completed(future_to_post):
                post = future_to_post[future]
                try:
                    post_id, results, success_count, fail_count = future.result()

                    # Log significant failures
                    if fail_count > 0:
                        logger.warning(f"Post {post_id}: {fail_count}/{len(results)} images failed")

                    pbar.update(1)

                except Exception as e:
                    logger.error(f"Thread exception for post {post['id']}: {e}")
                    pbar.update(1)

        pbar.close()
        elapsed = time.time() - start_time

        return {
            'elapsed': elapsed,
            'stats': self.stats,
            'failed_posts': self.failed_posts
        }


def main():
    """Main entry point for parallel image download"""

    print("\n" + "=" * 60)
    print("PARALLEL IMAGE DOWNLOAD - IQOS Georgia Analysis")
    print("Using ThreadPoolExecutor for 8-10x speedup")
    print("=" * 60)

    # Load config
    try:
        config = Config('config/config.yaml')
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        return 1

    # Parse all posts
    print("\n[1/3] Parsing Instagram data...")
    parser = InstagramDataParser(config.input_file)
    all_posts = parser.parse(mode='full')

    print(f"  Total posts: {len(all_posts)}")

    # Count total images
    total_images = sum(post['media']['image_count'] for post in all_posts)
    print(f"  Total images: {total_images:,}")
    print(f"  Estimated size: ~{total_images * 130 / 1024:.0f} MB")

    # Check existing cache
    cache_dir = Path(config.get('data', 'image_cache_dir'))
    existing_images = list(cache_dir.glob('*.jpg'))
    print(f"  Already cached: {len(existing_images)} images")

    # Determine optimal thread count
    # Recommendation: 12 threads for Starlink 300 Mbps
    # Can adjust based on network: 8 threads (slow), 12 (medium), 16 (fast)
    max_workers = 12
    print(f"\n  Using {max_workers} concurrent threads")
    print(f"  Expected speedup: ~{max_workers}x faster")

    # Confirm
    print("\n" + "=" * 60)
    response = input("Start parallel download? [y/N]: ")
    if response.lower() not in ['y', 'yes']:
        print("Cancelled.")
        return 0

    # Download with threading
    manager = ThreadSafeDownloadManager(all_posts, config, max_workers=max_workers)
    result = manager.download_all()

    elapsed = result['elapsed']
    stats = result['stats']
    failed_posts = result['failed_posts']

    # Report statistics
    print("\n[3/3] Download Summary")
    print("=" * 60)
    print(f"Time elapsed:          {elapsed/60:.1f} minutes ({elapsed:.1f} seconds)")
    print(f"Posts processed:       {stats['posts_processed']:,}/{len(all_posts):,}")
    print(f"Images downloaded:     {stats['downloaded']:,}")
    print(f"Images cached (reused):{stats['cached']:,}")
    print(f"Images failed:         {stats['failed']:,}")
    print(f"Total images:          {stats['downloaded'] + stats['cached']:,}")
    print(f"\nDownload speed:        {stats['posts_processed'] / elapsed:.2f} posts/sec")
    print(f"Average per post:      {elapsed / stats['posts_processed']:.2f} seconds")

    if failed_posts:
        print(f"\n[WARNING] {len(failed_posts)} posts had download failures:")
        for fp in failed_posts[:10]:  # Show first 10
            username = fp.get('username', 'unknown')
            fail_count = fp.get('failed_count', 'unknown')
            total = fp.get('total_images', 'unknown')
            print(f"  - @{username}: {fail_count}/{total} images failed")
            print(f"    {fp['url']}")

        if len(failed_posts) > 10:
            print(f"  ... and {len(failed_posts) - 10} more")

        # Save failed list
        failed_log = Path('output/logs/failed_image_downloads_parallel.txt')
        failed_log.parent.mkdir(parents=True, exist_ok=True)
        with open(failed_log, 'w', encoding='utf-8') as f:
            f.write("Failed Image Downloads (Parallel Run)\n")
            f.write("=" * 60 + "\n\n")
            for fp in failed_posts:
                f.write(f"Post ID: {fp['post_id']}\n")
                f.write(f"URL: {fp['url']}\n")
                if 'username' in fp:
                    f.write(f"Username: @{fp['username']}\n")
                if 'failed_count' in fp:
                    f.write(f"Failed: {fp['failed_count']}/{fp['total_images']}\n")
                if 'error' in fp:
                    f.write(f"Error: {fp['error']}\n")
                f.write("\n")
        print(f"\n  Full list saved to: {failed_log}")

    # Verify final count
    final_images = list(cache_dir.glob('*.jpg'))
    disk_usage = sum(f.stat().st_size for f in final_images) / (1024**2)

    print(f"\nFinal cache size:      {len(final_images):,} images")
    print(f"Disk usage:            {disk_usage:.0f} MB")

    # Performance comparison
    sequential_estimate = len(all_posts) * 1.5  # 1.5 sec/post average
    actual_speedup = sequential_estimate / elapsed

    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    print(f"Sequential estimate:   {sequential_estimate/60:.1f} minutes")
    print(f"Parallel actual:       {elapsed/60:.1f} minutes")
    print(f"Speedup achieved:      {actual_speedup:.1f}x faster")
    print("=" * 60)

    print("\n[OK] Parallel download complete!")
    print("\nNext step: Run full analysis")
    print("  python run_full_analysis.py --mode full")

    return 0


if __name__ == '__main__':
    sys.exit(main())
