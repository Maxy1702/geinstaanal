"""
IQOS Social Intelligence Analysis
Main entry point
"""
import logging
from pathlib import Path
import sys
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config_loader import Config
from json_parser import parse_instagram_data

# Setup logging
log_file = Path('output/logs/analysis.log')
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    
    logger.info("="*80)
    logger.info("IQOS Social Intelligence Analysis - Phase 1 Test")
    logger.info("="*80)
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = Config()
        logger.info(f"Mode: {config.get('processing', 'mode')}")
        logger.info(f"Input: {config.input_file.name}")
        
        if config.is_sample_mode:
            logger.info(f"Sample size: {config.sample_size}")
        
        # Parse Instagram data
        logger.info("\n" + "="*80)
        logger.info("Parsing Instagram Data")
        logger.info("="*80)
        
        posts, stats = parse_instagram_data(
            json_path=config.input_file,
            mode=config.get('processing', 'mode'),
            sample_size=config.sample_size
        )
        
        logger.info(f"\n📊 Parsing Statistics:")
        logger.info(f"  Total entries: {stats['total_entries']}")
        logger.info(f"  Valid posts: {stats['valid_posts']}")
        logger.info(f"  Error entries: {stats['error_entries']}")
        logger.info(f"  Skipped: {stats['skipped']}")
        logger.info(f"\n  By Type:")
        logger.info(f"    Images: {stats['by_type']['Image']}")
        logger.info(f"    Videos: {stats['by_type']['Video']}")
        logger.info(f"    Carousels: {stats['by_type']['Sidecar']}")
        logger.info(f"\n  📦 Selected for processing: {len(posts)} posts")
        
        # Show detailed sample
        logger.info("\n" + "="*80)
        logger.info("Sample Posts (Detailed)")
        logger.info("="*80)
        
        for i, post in enumerate(posts[:3]):
            logger.info(f"\n{'='*60}")
            logger.info(f"Post {i+1}/{len(posts)}")
            logger.info(f"{'='*60}")
            logger.info(f"ID: {post['id']}")
            logger.info(f"Type: {post['type']}")
            logger.info(f"URL: {post['url']}")
            logger.info(f"Owner: @{post['owner']['username']} ({post['owner']['full_name']})")
            logger.info(f"Date: {post['timestamp'][:10]}")
            
            # Content
            caption = post['content']['caption']
            logger.info(f"\nCaption: {caption[:100]}{'...' if len(caption) > 100 else ''}")
            logger.info(f"Hashtags: {len(post['content']['hashtags'])}")
            logger.info(f"Mentions: {len(post['content']['mentions'])}")
            
            # Engagement
            likes = post['engagement']['likes']
            likes_str = "Hidden" if post['engagement']['likes_hidden'] else f"{likes:,}"
            logger.info(f"\nEngagement:")
            logger.info(f"  Likes: {likes_str}")
            logger.info(f"  Comments: {post['engagement']['comments_count']}")
            if post['engagement'].get('video_views'):
                logger.info(f"  Video Views: {post['engagement']['video_views']:,}")
            
            # Media
            logger.info(f"\nMedia:")
            logger.info(f"  Images: {post['media']['image_count']}")
            logger.info(f"  Is Video: {post['media']['is_video']}")
            if post['media']['images']:
                logger.info(f"  First Image URL: {post['media']['images'][0][:60]}...")
            
            # Comments
            logger.info(f"\nComments: {len(post['comments'])} extracted")
            if post['comments']:
                first_comment = post['comments'][0]
                comment_text = first_comment['text'][:80]
                logger.info(f"  First: {comment_text}{'...' if len(first_comment['text']) > 80 else ''}")
            
            # Location
            if post['location']:
                logger.info(f"\nLocation: {post['location']['name']}")
        
        # Save sample output
        output_file = Path('output/sample_parsed_posts.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(posts[:5], f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Sample output saved to: {output_file}")
        logger.info(f"✅ Phase 1 Test Complete!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()