"""
Analysis Orchestrator - Main pipeline for Instagram post analysis
Coordinates parsing, image download, LLM analysis, and progress tracking
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
import signal
import sys
import concurrent.futures

from tqdm import tqdm

from .json_parser import InstagramDataParser
from .image_handler import ImageDownloader, ImageCache
from .llm_client import LLMClient
from .prompts import get_system_prompt, build_user_prompt, get_expected_schema_description
from .config_loader import Config

logger = logging.getLogger(__name__)


class AnalysisState:
    """Manage analysis progress and checkpointing"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load existing state or create new"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    logger.info(f"Loaded checkpoint: {state['processed_count']} posts already analyzed")
                    return state
            except Exception as e:
                logger.warning(f"Could not load state file: {e}. Starting fresh.")

        return {
            'version': '1.0',
            'started_at': datetime.now().isoformat(),
            'last_saved': None,
            'processed_count': 0,
            'processed_ids': [],
            'failed_ids': [],
            'results': [],
            'statistics': {
                'total_posts': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'nicotine_detected': 0,
                'by_category': {}
            }
        }

    def save(self):
        """Save current state to disk"""
        self.state['last_saved'] = datetime.now().isoformat()
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            logger.debug(f"Checkpoint saved: {self.state['processed_count']} posts")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def is_processed(self, post_id: str) -> bool:
        """Check if post already processed"""
        return post_id in self.state['processed_ids']

    def mark_processed(self, post_id: str, result: Dict[str, Any], success: bool = True):
        """Mark post as processed and store result"""
        if success:
            self.state['processed_ids'].append(post_id)
            self.state['results'].append(result)
            self.state['statistics']['successful'] += 1

            # Track nicotine detection
            if result.get('analysis', {}).get('nicotine_detection', {}).get('detected'):
                self.state['statistics']['nicotine_detected'] += 1

                # Track by category
                products = result.get('analysis', {}).get('nicotine_detection', {}).get('products', [])
                for product in products:
                    category = product.get('category', 'Unknown')
                    self.state['statistics']['by_category'][category] = \
                        self.state['statistics']['by_category'].get(category, 0) + 1
        else:
            self.state['failed_ids'].append(post_id)
            self.state['statistics']['failed'] += 1

        self.state['processed_count'] += 1

    def get_results(self) -> List[Dict[str, Any]]:
        """Get all analysis results"""
        return self.state['results']

    def get_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        return self.state['statistics']


class AnalysisOrchestrator:
    """Main orchestrator for Instagram post analysis pipeline"""

    def __init__(self, config: Config):
        """
        Initialize orchestrator

        Args:
            config: Configuration object
        """
        self.config = config
        self.shutdown_requested = False

        # Setup logging
        self._setup_logging()

        # Initialize components
        logger.info("Initializing analysis pipeline...")

        self.parser = InstagramDataParser(config.input_file)

        self.image_downloader = ImageDownloader(
            cache_dir=Path(config.get('data', 'image_cache_dir')),
            timeout=30,
            max_retries=3
        )

        self.image_cache = ImageCache(
            cache_dir=Path(config.get('data', 'image_cache_dir'))
        )

        self.llm_client = LLMClient(
            api_endpoint=config.get('llm', 'api_endpoint'),
            model_name=config.get('llm', 'model_name'),
            timeout=config.get('llm', 'timeout') or 120,
            max_retries=config.get('llm', 'max_retries') or 3,
            temperature=config.get('llm', 'temperature') or 0.3
        )

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(" Pipeline initialized successfully")

    def _setup_logging(self):
        """Configure logging"""
        log_level = self.config.get('progress', 'log_level') or 'INFO'
        log_file = Path('output/logs') / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s - %(message)s'
        ))

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        logger.info(f"Logging to: {log_file}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals (Ctrl+C)"""
        logger.warning("\n  Shutdown signal received. Saving progress...")
        self.shutdown_requested = True

    def run_analysis(self) -> Dict[str, Any]:
        """
        Run full analysis pipeline

        Returns:
            Analysis results and statistics
        """
        start_time = time.time()

        try:
            # Step 1: Parse posts
            logger.info("=" * 60)
            logger.info("STEP 1: Parsing Instagram data")
            logger.info("=" * 60)

            mode = 'sample' if self.config.is_sample_mode else 'full'
            sample_size = self.config.sample_size if self.config.is_sample_mode else None

            posts = self.parser.parse(mode=mode, sample_size=sample_size)
            parse_stats = self.parser.get_stats()

            logger.info(f" Parsed {len(posts)} posts")
            logger.info(f"   Images: {parse_stats['by_type']['Image']}")
            logger.info(f"   Videos: {parse_stats['by_type']['Video']}")
            logger.info(f"   Carousels: {parse_stats['by_type']['Sidecar']}")

            if len(posts) == 0:
                logger.error("No posts to analyze. Exiting.")
                return {'status': 'error', 'message': 'No posts found'}

            # Step 2: Initialize state
            logger.info("\n" + "=" * 60)
            logger.info("STEP 2: Initializing analysis state")
            logger.info("=" * 60)

            state_file = Path(self.config.get('data', 'processed_state_dir')) / 'analysis_state.json'
            self.state = AnalysisState(state_file)
            self.state.state['statistics']['total_posts'] = len(posts)

            # Check resume
            already_processed = len(self.state.state['processed_ids'])
            if already_processed > 0:
                logger.info(f"= Resuming from checkpoint: {already_processed} posts already done")

            # Step 3: Test LLM connection
            logger.info("\n" + "=" * 60)
            logger.info("STEP 3: Testing LLM connection")
            logger.info("=" * 60)

            if not self.llm_client.test_connection():
                logger.error("L Cannot connect to LM Studio. Please ensure:")
                logger.error("   1. LM Studio is running")
                logger.error("   2. Model is loaded (Gemma 3 12B)")
                logger.error("   3. Server is started")
                logger.error(f"   4. Endpoint is correct: {self.config.get('llm', 'api_endpoint')}")
                return {'status': 'error', 'message': 'LLM connection failed'}

            logger.info(" LLM connection successful")

            # Step 4: Process posts
            logger.info("\n" + "=" * 60)
            logger.info("STEP 4: Analyzing posts")
            logger.info("=" * 60)

            results = self._process_posts(posts)

            # Step 5: Final statistics
            logger.info("\n" + "=" * 60)
            logger.info("STEP 5: Analysis complete")
            logger.info("=" * 60)

            elapsed = time.time() - start_time
            stats = self._generate_final_statistics(elapsed)

            logger.info(f"\n Analysis completed successfully in {elapsed/60:.1f} minutes")
            logger.info(f"   Successful: {stats['successful']}/{stats['total_posts']}")
            logger.info(f"   Failed: {stats['failed']}")
            logger.info(f"   Nicotine detected: {stats['nicotine_detected']} ({stats['detection_rate']:.1f}%)")

            if stats['by_category']:
                logger.info(f"\n   Breakdown by category:")
                for category, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
                    logger.info(f"      {category}: {count}")

            return {
                'status': 'success',
                'results': results,
                'statistics': stats,
                'elapsed_time': elapsed
            }

        except Exception as e:
            logger.error(f"L Analysis failed with error: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

        finally:
            # Cleanup
            self.image_downloader.close()

    def _analyze_single_post_with_timeout(
        self,
        post: Dict[str, Any],
        username: str,
        post_id: str,
        system_prompt: str,
        download_enabled: bool,
        max_images: int
    ) -> tuple:
        """
        Process a single post with timeout protection (90 seconds)

        Returns:
            tuple: (status, result) where status is 'success', 'failed', or 'error'
        """
        try:
            # Download images if needed
            image_paths = []
            if download_enabled and post['media']['images']:
                image_results = self.image_downloader.download_post_images(
                    post_id=post_id,
                    image_urls=post['media']['images'],
                    max_images=max_images
                )

                # Collect successful downloads
                image_paths = [
                    r['local_path'] for r in image_results
                    if r['success'] and r['local_path']
                ]

                if not image_paths and post['media']['images']:
                    logger.warning(f"    No images downloaded for post {post_id}")

            # Build prompt
            user_prompt = build_user_prompt(post)

            # Analyze with LLM
            analysis_result = self.llm_client.analyze_post(
                post=post,
                image_paths=image_paths,
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            if analysis_result:
                # Success
                result = {
                    'post_id': post_id,
                    'username': username,
                    'url': post['url'],
                    'timestamp': post['timestamp'],
                    'post_type': post['type'],
                    'analyzed_at': datetime.now().isoformat(),
                    'image_count': len(image_paths),
                    'analysis': analysis_result
                }
                return ('success', result)
            else:
                return ('failed', f"Analysis returned None for post {post_id}")

        except Exception as e:
            return ('error', f"Error processing post {post_id}: {str(e)}")

    def _process_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process all posts through the analysis pipeline

        Args:
            posts: List of normalized posts

        Returns:
            List of analysis results
        """
        save_interval = self.config.get('progress', 'save_interval') or 10
        max_images = self.config.get('images', 'max_images_per_post') or 10
        download_enabled = self.config.get('images', 'download_enabled')
        if download_enabled is None:
            download_enabled = True

        # Build system prompt once
        system_prompt = get_system_prompt() + get_expected_schema_description()

        # Process with progress bar
        with tqdm(total=len(posts), desc="Analyzing posts", unit="post") as pbar:
            for idx, post in enumerate(posts):
                # Update progress bar
                if idx > 0:
                    pbar.update(1)

                # Check for shutdown
                if self.shutdown_requested:
                    logger.warning("  Shutdown requested. Saving progress and exiting...")
                    self.state.save()
                    break

                post_id = post['id']
                username = post['owner']['username']

                # Skip if already processed
                if self.state.is_processed(post_id):
                    logger.debug(f"Skipping post {post_id} (already processed)")
                    self.state.state['statistics']['skipped'] += 1
                    continue

                # Process this post
                try:
                    pbar.set_description(f"Analyzing @{username}")

                    # Download images if needed
                    image_paths = []
                    if download_enabled and post['media']['images']:
                        image_results = self.image_downloader.download_post_images(
                            post_id=post_id,
                            image_urls=post['media']['images'],
                            max_images=max_images
                        )

                        # Collect successful downloads
                        image_paths = [
                            r['local_path'] for r in image_results
                            if r['success'] and r['local_path']
                        ]

                        if not image_paths and post['media']['images']:
                            logger.warning(f"    No images downloaded for post {post_id}")

                    # Build prompt
                    user_prompt = build_user_prompt(post)

                    # Analyze with LLM
                    analysis_result = self.llm_client.analyze_post(
                        post=post,
                        image_paths=image_paths,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt
                    )

                    if analysis_result:
                        # Success
                        result = {
                            'post_id': post_id,
                            'username': username,
                            'url': post['url'],
                            'timestamp': post['timestamp'],
                            'post_type': post['type'],
                            'analyzed_at': datetime.now().isoformat(),
                            'image_count': len(image_paths),
                            'analysis': analysis_result
                        }

                        self.state.mark_processed(post_id, result, success=True)
                        logger.debug(f"   Post {post_id} analyzed successfully")

                    else:
                        # Analysis failed
                        logger.warning(f"  L Analysis failed for post {post_id}")
                        self.state.mark_processed(post_id, {}, success=False)

                except Exception as e:
                    logger.error(f"  L Error processing post {post_id}: {e}", exc_info=True)
                    self.state.mark_processed(post_id, {}, success=False)

                # Periodic checkpoint save
                if (idx + 1) % save_interval == 0:
                    self.state.save()
                    logger.debug(f"Checkpoint: {idx + 1}/{len(posts)} posts processed")

            # Final update
            pbar.update(1)

        # Final save
        self.state.save()
        logger.info("= Final checkpoint saved")

        return self.state.get_results()

    def _generate_final_statistics(self, elapsed_time: float) -> Dict[str, Any]:
        """
        Generate comprehensive statistics

        Args:
            elapsed_time: Total elapsed time in seconds

        Returns:
            Statistics dictionary
        """
        state_stats = self.state.get_statistics()
        llm_stats = self.llm_client.get_stats()
        image_stats = self.image_downloader.get_stats()

        total_posts = state_stats['total_posts']
        successful = state_stats['successful']
        nicotine_detected = state_stats['nicotine_detected']

        detection_rate = (nicotine_detected / successful * 100) if successful > 0 else 0
        avg_time_per_post = elapsed_time / successful if successful > 0 else 0

        return {
            'total_posts': total_posts,
            'successful': successful,
            'failed': state_stats['failed'],
            'skipped': state_stats['skipped'],
            'nicotine_detected': nicotine_detected,
            'detection_rate': detection_rate,
            'by_category': state_stats['by_category'],

            'timing': {
                'total_seconds': elapsed_time,
                'total_minutes': elapsed_time / 60,
                'avg_seconds_per_post': avg_time_per_post
            },

            'llm': {
                'total_requests': llm_stats['total_requests'],
                'successful_requests': llm_stats['successful_requests'],
                'failed_requests': llm_stats['failed_requests'],
                'retry_count': llm_stats['retry_count'],
                'success_rate': llm_stats['success_rate'],
                'total_tokens': llm_stats['total_tokens']
            },

            'images': {
                'downloaded': image_stats['downloaded'],
                'cached': image_stats['cached'],
                'failed': image_stats['failed'],
                'total_attempts': image_stats['total_attempts']
            }
        }

    def export_results(self, output_path: Optional[Path] = None) -> Path:
        """
        Export analysis results to JSON file

        Args:
            output_path: Optional custom output path

        Returns:
            Path to exported file
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = Path(self.config.get('data', 'output_dir')) / f'analysis_results_{timestamp}.json'

        output_path.parent.mkdir(parents=True, exist_ok=True)

        results = self.state.get_results()
        statistics = self.state.get_statistics()

        export_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'config_mode': 'sample' if self.config.is_sample_mode else 'full',
                'total_posts': len(results)
            },
            'statistics': statistics,
            'results': results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"= Results exported to: {output_path}")
        return output_path


def run_analysis_pipeline(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Convenience function to run complete analysis pipeline

    Args:
        config_path: Path to configuration file

    Returns:
        Analysis results and statistics
    """
    # Load config
    config = Config(config_path)

    logger.info("=" * 60)
    logger.info("IQOS GEORGIA SOCIAL INTELLIGENCE ANALYSIS")
    logger.info("=" * 60)
    logger.info(f"Mode: {config.get('processing', 'mode').upper()}")
    if config.is_sample_mode:
        logger.info(f"Sample size: {config.sample_size}")
    logger.info(f"Input file: {config.input_file.name}")
    logger.info(f"LLM endpoint: {config.get('llm', 'api_endpoint')}")
    logger.info(f"Model: {config.get('llm', 'model_name')}")
    logger.info("=" * 60 + "\n")

    # Run analysis
    orchestrator = AnalysisOrchestrator(config)
    results = orchestrator.run_analysis()

    # Export results if successful
    if results['status'] == 'success':
        orchestrator.export_results()

    return results
