"""
Quick Status Check - One-time snapshot of analysis progress
"""
import json
from pathlib import Path
from datetime import datetime

def check_status():
    """Check and display current status"""
    print("=" * 70)
    print("IQOS ANALYSIS - QUICK STATUS CHECK")
    print("=" * 70)
    print()

    # Check checkpoint
    checkpoint_file = Path('data/processed/analysis_state.json')
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            processed = state.get('processed_count', 0)
            failed = len(state.get('failed_ids', []))
            total = 2593

            print(f"STATUS: Analysis in progress")
            print(f"  Posts processed:  {processed:,} / {total:,} ({processed/total*100:.1f}%)")
            print(f"  Successful:       {processed - failed:,}")
            print(f"  Failed:           {failed:,}")
            print()

            if 'detection_stats' in state:
                stats = state['detection_stats']
                detections = stats.get('total_detections', 0)
                print(f"DETECTIONS:")
                print(f"  Total detected:   {detections}")
                print(f"  Detection rate:   {detections/processed*100:.1f}%" if processed > 0 else "  Calculating...")
                print()

            last_saved = state.get('last_saved', 'Unknown')
            print(f"  Last update:      {last_saved}")
            print()

        except Exception as e:
            print(f"ERROR: Could not read checkpoint: {e}")
            print()
    else:
        print("STATUS: Not started yet")
        print("  No checkpoint file found")
        print()

    # Check images
    image_dir = Path('data/images')
    if image_dir.exists():
        image_count = len(list(image_dir.glob('*.*')))
        print(f"IMAGES: {image_count:,} cached")
    else:
        print("IMAGES: Directory not found")

    # Check latest results
    results_dir = Path('output/reports')
    if results_dir.exists():
        result_files = sorted(results_dir.glob('analysis_results_*.json'),
                            key=lambda x: x.stat().st_mtime, reverse=True)
        if result_files:
            latest = result_files[0]
            print(f"\nLATEST RESULTS: {latest.name}")
            try:
                with open(latest, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                    stats = results.get('statistics', {})
                    print(f"  Posts analyzed:   {stats.get('total_posts', 0)}")
                    print(f"  Detections:       {stats.get('nicotine_detected', 0)}")
                    print(f"  Success rate:     {stats.get('successful', 0)}/{stats.get('total_posts', 0)}")
            except:
                pass

    print()
    print("=" * 70)

if __name__ == '__main__':
    check_status()
