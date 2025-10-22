"""
IQOS Georgia Social Intelligence Analysis - Main Entry Point
Run complete analysis pipeline: parsing → image download → LLM analysis → results export
"""
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.analyzer import run_analysis_pipeline
from src.config_loader import Config


def main():
    """Main entry point with CLI argument parsing"""

    parser = argparse.ArgumentParser(
        description='IQOS Georgia Social Intelligence Analysis Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run sample mode (50 posts, uses config.yaml setting)
  python run_full_analysis.py

  # Run full analysis (all 2,629 posts)
  python run_full_analysis.py --mode full

  # Run sample with custom size
  python run_full_analysis.py --mode sample --sample-size 100

  # Use custom config file
  python run_full_analysis.py --config my_config.yaml

Prerequisites:
  1. LM Studio running with Gemma 3 12B loaded
  2. Server started in LM Studio (http://127.0.0.1:512/v1)
  3. Input JSON file present (see config.yaml)
  4. Virtual environment activated
        """
    )

    parser.add_argument(
        '--mode',
        choices=['sample', 'full'],
        help='Analysis mode: sample (default from config) or full (all posts)'
    )

    parser.add_argument(
        '--sample-size',
        type=int,
        help='Number of posts for sample mode (overrides config)'
    )

    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )

    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous checkpoint (automatic if checkpoint exists)'
    )

    args = parser.parse_args()

    # Load config
    try:
        config = Config(args.config)
    except Exception as e:
        print(f"[ERROR] Error loading configuration: {e}")
        print(f"   Config file: {args.config}")
        return 1

    # Override config with CLI arguments
    if args.mode:
        config.config['processing']['mode'] = args.mode
        print(f"Mode override: {args.mode}")

    if args.sample_size:
        config.config['processing']['sample_size'] = args.sample_size
        print(f"Sample size override: {args.sample_size}")

    # Display configuration summary
    print("\n" + "=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    print(f"Mode:           {config.get('processing', 'mode').upper()}")
    if config.is_sample_mode:
        print(f"Sample Size:    {config.sample_size}")
    print(f"Input File:     {config.input_file}")
    print(f"Image Cache:    {config.get('data', 'image_cache_dir')}")
    print(f"Output Dir:     {config.get('data', 'output_dir')}")
    print(f"LLM Endpoint:   {config.get('llm', 'api_endpoint')}")
    print(f"Model:          {config.get('llm', 'model_name')}")
    print(f"Checkpoint:     {'Enabled' if args.resume else 'Auto-resume if exists'}")
    print("=" * 60)

    # Confirm for full mode
    if config.get('processing', 'mode') == 'full':
        print("\n[WARNING]  FULL MODE: Will analyze all 2,629 posts (~3-4 hours)")
        response = input("Continue? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return 0

    # Run analysis
    print("\n[START] Starting analysis pipeline...\n")

    try:
        # Pass the config object directly to preserve overrides
        from src.analyzer import AnalysisOrchestrator
        orchestrator = AnalysisOrchestrator(config)
        results = orchestrator.run_analysis()

        if results['status'] == 'success':
            # Export results
            orchestrator.export_results()

            print("\n" + "=" * 60)
            print("[OK] ANALYSIS COMPLETED SUCCESSFULLY")
            print("=" * 60)

            stats = results['statistics']
            print(f"\nProcessed:         {stats['successful']}/{stats['total_posts']} posts")
            print(f"Failed:            {stats['failed']}")
            print(f"Nicotine detected: {stats['nicotine_detected']} ({stats['detection_rate']:.1f}%)")
            print(f"Time elapsed:      {stats['timing']['total_minutes']:.1f} minutes")
            print(f"Avg per post:      {stats['timing']['avg_seconds_per_post']:.1f} seconds")

            if stats['by_category']:
                print("\nDetection breakdown:")
                for category, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
                    print(f"  {category:20} {count:4d}")

            print("\nLLM Statistics:")
            print(f"  Total requests:    {stats['llm']['total_requests']}")
            print(f"  Successful:        {stats['llm']['successful_requests']}")
            print(f"  Failed:            {stats['llm']['failed_requests']}")
            print(f"  Success rate:      {stats['llm']['success_rate']:.1%}")
            print(f"  Total tokens:      {stats['llm']['total_tokens']:,}")

            print("\nImage Statistics:")
            print(f"  Downloaded:        {stats['images']['downloaded']}")
            print(f"  Cached (reused):   {stats['images']['cached']}")
            print(f"  Failed:            {stats['images']['failed']}")

            print("\n[FILE] Results exported to: output/reports/")
            print("=" * 60)

            return 0
        else:
            print("\n" + "=" * 60)
            print("[ERROR] ANALYSIS FAILED")
            print("=" * 60)
            print(f"Error: {results.get('message', 'Unknown error')}")
            print("\nCheck the log file in output/logs/ for details")
            print("=" * 60)
            return 1

    except KeyboardInterrupt:
        print("\n\n[WARNING]  Analysis interrupted by user")
        print("Progress has been saved. Run again to resume from checkpoint.")
        return 130

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
