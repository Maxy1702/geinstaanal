"""
Test if LM Studio can handle concurrent requests for parallel processing
"""
import requests
import time
import concurrent.futures
import json

def test_simple_request(request_id):
    """Send a simple test request"""
    start = time.time()

    payload = {
        "model": "google/gemma-3-12b",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Respond in 10 words or less."
            },
            {
                "role": "user",
                "content": f"Say 'Test {request_id} complete'"
            }
        ],
        "temperature": 0.3,
        "max_tokens": 50
    }

    try:
        response = requests.post(
            "http://127.0.0.1:512/v1/chat/completions",
            json=payload,
            timeout=30
        )

        elapsed = time.time() - start

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return {
                'id': request_id,
                'success': True,
                'time': elapsed,
                'response': content
            }
        else:
            return {
                'id': request_id,
                'success': False,
                'time': elapsed,
                'error': f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            'id': request_id,
            'success': False,
            'time': time.time() - start,
            'error': str(e)
        }

def main():
    print("=" * 60)
    print("CONCURRENT REQUEST TEST")
    print("=" * 60)
    print()

    # Test 1: Sequential baseline
    print("Test 1: Sequential (2 requests)")
    start = time.time()
    results_seq = []
    for i in range(2):
        result = test_simple_request(i)
        results_seq.append(result)
        print(f"  Request {i}: {result['time']:.1f}s - {result.get('response', result.get('error'))}")
    sequential_time = time.time() - start
    print(f"Total time: {sequential_time:.1f}s")
    print()

    # Test 2: Parallel
    print("Test 2: Parallel (2 requests simultaneously)")
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(test_simple_request, i) for i in range(2, 4)]
        results_par = [f.result() for f in concurrent.futures.as_completed(futures)]
    parallel_time = time.time() - start

    for result in results_par:
        print(f"  Request {result['id']}: {result['time']:.1f}s - {result.get('response', result.get('error'))}")
    print(f"Total time: {parallel_time:.1f}s")
    print()

    # Analysis
    print("=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    if all(r['success'] for r in results_par):
        speedup = sequential_time / parallel_time
        print(f"Sequential time: {sequential_time:.1f}s")
        print(f"Parallel time:   {parallel_time:.1f}s")
        print(f"Speedup:         {speedup:.2f}x")
        print()

        if speedup > 1.5:
            print("[OK] LM Studio supports concurrent requests!")
            print("     Parallel processing is feasible.")
        elif speedup > 1.1:
            print("[MAYBE] Some parallelization benefit, but limited.")
            print("        LM Studio might be queueing requests.")
        else:
            print("[NO] LM Studio is serializing requests.")
            print("     Parallel processing won't help.")
    else:
        print("[ERROR] Some parallel requests failed.")
        print("        LM Studio may not support concurrent requests.")

if __name__ == '__main__':
    main()
