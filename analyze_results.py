"""
Quick analysis script for comparing detection results
"""
import json
from pathlib import Path
from collections import Counter

def analyze_results(json_path):
    """Analyze detection results from JSON output"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stats = data['statistics']
    results = data['results']

    print(f"\n{'='*80}")
    print(f"ANALYSIS RESULTS: {json_path.name}")
    print(f"Generated: {data['metadata']['generated_at']}")
    print(f"{'='*80}\n")

    # Overview
    print(f"[OVERVIEW]")
    print(f"  Total Posts:     {stats['total_posts']}")
    print(f"  Successful:      {stats['successful']}")
    print(f"  Failed:          {stats['failed']}")
    print(f"  Nicotine Detected: {stats['nicotine_detected']} ({stats['nicotine_detected']/stats['total_posts']*100:.1f}%)")
    print()

    # Category breakdown
    print(f"[DETECTION BY CATEGORY]")
    for category, count in stats.get('by_category', {}).items():
        print(f"  {category:20s}: {count}")
    print()

    # Detailed detections
    detections = [r for r in results if r['analysis']['nicotine_detection']['detected']]

    if detections:
        print(f"[DETECTED POSTS]")
        for i, det in enumerate(detections, 1):
            nd = det['analysis']['nicotine_detection']
            print(f"\n  {i}. @{det['username']} - {det['url']}")
            print(f"     Confidence: {nd['confidence']}")

            for product in nd.get('products', []):
                print(f"     Product: {product['category']}", end='')
                if product.get('specific_brand'):
                    print(f" - {product['specific_brand']}", end='')
                if product.get('specific_model'):
                    print(f" ({product['specific_model']})", end='')
                print()

            # Show visual evidence
            if nd['detection_evidence'].get('visual'):
                print(f"     Visual: {nd['detection_evidence']['visual'][0][:100]}...")

    # Fire emoji check
    print(f"\n{'='*80}")
    print(f"[FIRE EMOJI CHECK]")
    fire_emoji_posts = []
    for r in results:
        emoji_examples = r['analysis']['sentiment'].get('emoji_usage', {}).get('examples', [])
        if '🔥' in emoji_examples or 'fire' in str(emoji_examples).lower():
            detected = r['analysis']['nicotine_detection']['detected']
            fire_emoji_posts.append({
                'username': r['username'],
                'url': r['url'],
                'detected': detected,
                'emojis': emoji_examples
            })

    print(f"  Posts with fire emoji: {len(fire_emoji_posts)}")
    print(f"  Incorrectly flagged as nicotine: {sum(1 for p in fire_emoji_posts if p['detected'])}")

    if fire_emoji_posts:
        print(f"\n  Details:")
        for p in fire_emoji_posts[:5]:  # Show first 5
            status = "FLAGGED" if p['detected'] else "OK"
            # Convert emojis to safe representation
            emojis_str = str(p['emojis']).encode('ascii', 'replace').decode('ascii')
            print(f"    [{status}] @{p['username']} - {emojis_str}")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    reports_dir = Path('output/reports')

    # Find the two most recent JSON files
    json_files = sorted(reports_dir.glob('analysis_results_*.json'),
                       key=lambda p: p.stat().st_mtime,
                       reverse=True)

    if len(json_files) >= 2:
        print("\n[COMPARING TWO MOST RECENT RUNS]")
        print(f"Run 1 (older):  {json_files[1].name}")
        print(f"Run 2 (latest): {json_files[0].name}")

        analyze_results(json_files[1])
        analyze_results(json_files[0])

        # Compare detection rates
        with open(json_files[1], 'r', encoding='utf-8') as f:
            data1 = json.load(f)
        with open(json_files[0], 'r', encoding='utf-8') as f:
            data2 = json.load(f)

        rate1 = data1['statistics']['nicotine_detected'] / data1['statistics']['total_posts'] * 100
        rate2 = data2['statistics']['nicotine_detected'] / data2['statistics']['total_posts'] * 100

        print(f"\n[COMPARISON]")
        print(f"  Run 1 detection rate: {rate1:.1f}%")
        print(f"  Run 2 detection rate: {rate2:.1f}%")
        print(f"  Change: {rate2-rate1:+.1f} percentage points")

        if rate2 < rate1:
            print(f"  [SUCCESS] Detection rate decreased (fewer false positives)")
        elif rate2 > rate1:
            print(f"  [WARNING] Detection rate increased")
        else:
            print(f"  [NEUTRAL] No change in detection rate")

    elif len(json_files) == 1:
        analyze_results(json_files[0])
    else:
        print("No result files found in output/reports/")
