"""
Real-time Analysis Progress Monitor
Displays live statistics and progress for IQOS analysis pipeline
"""
import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
import sys

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def load_checkpoint():
    """Load current analysis state"""
    checkpoint_file = Path('data/processed/analysis_state.json')
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def calculate_eta(processed, total, elapsed_seconds):
    """Calculate estimated time remaining"""
    if processed == 0:
        return "Calculating..."

    rate = processed / elapsed_seconds
    remaining = total - processed
    eta_seconds = remaining / rate if rate > 0 else 0

    return str(timedelta(seconds=int(eta_seconds)))

def format_time(seconds):
    """Format seconds to readable time"""
    return str(timedelta(seconds=int(seconds)))

def get_latest_log_lines(n=10):
    """Get last n lines from latest log file"""
    log_dir = Path('output/logs')
    if not log_dir.exists():
        return []

    log_files = sorted(log_dir.glob('analysis_*.log'), key=lambda x: x.stat().st_mtime, reverse=True)
    if not log_files:
        return []

    try:
        with open(log_files[0], 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return lines[-n:]
    except:
        return []

def monitor_loop():
    """Main monitoring loop"""
    start_time = time.time()
    last_count = 0

    while True:
        clear_screen()

        # Load current state
        state = load_checkpoint()
        elapsed = time.time() - start_time

        print("=" * 80)
        print("IQOS ANALYSIS - LIVE MONITORING DASHBOARD")
        print("=" * 80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Elapsed: {format_time(elapsed)}")
        print("=" * 80)

        if state:
            processed = state.get('processed_count', 0)
            failed = len(state.get('failed_ids', []))
            total = 2593  # Posts with images

            # Progress bar
            progress_pct = (processed / total * 100) if total > 0 else 0
            bar_width = 50
            filled = int(bar_width * processed / total) if total > 0 else 0
            bar = '█' * filled + '░' * (bar_width - filled)

            print(f"\nPROGRESS: [{bar}] {progress_pct:.1f}%")
            print(f"Posts: {processed:,} / {total:,}")
            print()

            # Statistics
            print("STATISTICS:")
            print(f"  Successful:      {processed - failed:,}")
            print(f"  Failed:          {failed:,}")
            print(f"  Remaining:       {total - processed:,}")
            print()

            # Performance
            if processed > last_count:
                rate = processed / elapsed if elapsed > 0 else 0
                print("PERFORMANCE:")
                print(f"  Processing rate: {rate:.2f} posts/sec")
                print(f"  Avg time/post:   {elapsed/processed:.1f} seconds" if processed > 0 else "  Calculating...")
                print()

                # ETA
                eta = calculate_eta(processed, total, elapsed)
                print("TIME ESTIMATE:")
                print(f"  ETA to completion: {eta}")
                print(f"  Estimated finish:  {(datetime.now() + timedelta(seconds=(total-processed)/(rate if rate > 0 else 1))).strftime('%H:%M:%S')}")
                print()

            # Detection stats (if available)
            if 'detection_stats' in state:
                stats = state['detection_stats']
                print("DETECTION SUMMARY:")
                print(f"  Detections: {stats.get('total_detections', 0)}")
                print(f"  Detection rate: {stats.get('total_detections', 0)/processed*100:.1f}%" if processed > 0 else "  Calculating...")
                print()

            # Last update
            last_saved = state.get('last_saved', 'Unknown')
            if last_saved != 'Unknown':
                try:
                    last_dt = datetime.fromisoformat(last_saved)
                    seconds_ago = (datetime.now() - last_dt).total_seconds()
                    print(f"Last checkpoint: {int(seconds_ago)}s ago")
                except:
                    print(f"Last checkpoint: {last_saved}")

            last_count = processed

        else:
            print("\nWaiting for analysis to start...")
            print("  Status: No checkpoint file found")
            print("  Expected file: data/processed/analysis_state.json")
            print()
            print("  To start analysis:")
            print("    python run_full_analysis.py --mode full")

        print("\n" + "=" * 80)
        print("RECENT LOG ACTIVITY:")
        print("=" * 80)

        # Show recent log lines
        log_lines = get_latest_log_lines(8)
        if log_lines:
            for line in log_lines:
                # Clean up line
                line = line.strip()
                if line:
                    # Truncate long lines
                    if len(line) > 78:
                        line = line[:75] + "..."
                    print(f"  {line}")
        else:
            print("  No log activity yet")

        print("\n" + "=" * 80)
        print("Press Ctrl+C to exit monitoring")
        print("=" * 80)

        # Update every 2 seconds
        time.sleep(2)

if __name__ == '__main__':
    print("Starting live analysis monitor...")
    print("This will refresh every 2 seconds")
    print()

    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
