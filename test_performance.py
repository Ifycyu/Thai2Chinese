"""Performance test script for ThaiWord API."""
import requests
import time
import json

BASE_URL = "http://localhost:8082"
SENTENCE = "สวัสดีครับ"

def test_with_session():
    """Test with session (like browser - reuses connection)."""
    session = requests.Session()
    times = []

    for i in range(3):
        start = time.time()
        resp = session.post(f"{BASE_URL}/api/v1/analyze?sentence={SENTENCE}")
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Session request {i+1}: {elapsed:.3f}s")

    return times

def test_without_session():
    """Test without session (like curl - new connection each time)."""
    times = []

    for i in range(3):
        start = time.time()
        resp = requests.post(f"{BASE_URL}/api/v1/analyze?sentence={SENTENCE}")
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  No-session request {i+1}: {elapsed:.3f}s")

    return times

def test_internal_vs_external():
    """Test internal vs external endpoint."""
    session = requests.Session()

    # Internal endpoint (used by browser)
    start = time.time()
    resp1 = session.post(f"{BASE_URL}/api/analyze?sentence={SENTENCE}")
    internal_time = time.time() - start

    # External endpoint
    start = time.time()
    resp2 = session.post(f"{BASE_URL}/api/v1/analyze?sentence={SENTENCE}")
    external_time = time.time() - start

    print(f"  Internal /api/analyze: {internal_time:.3f}s")
    print(f"  External /api/v1/analyze: {external_time:.3f}s")

    return internal_time, external_time

def main():
    print("=" * 50)
    print("ThaiWord API Performance Test")
    print("=" * 50)
    print(f"Sentence: [Thai sentence]")
    print()

    # Test 1: With session
    print("Test 1: With Session (browser-like)")
    session_times = test_with_session()
    print(f"  Average: {sum(session_times)/len(session_times):.3f}s")
    print()

    # Test 2: Without session
    print("Test 2: Without Session (curl-like)")
    no_session_times = test_without_session()
    print(f"  Average: {sum(no_session_times)/len(no_session_times):.3f}s")
    print()

    # Test 3: Internal vs External
    print("Test 3: Internal vs External endpoint")
    internal_time, external_time = test_internal_vs_external()
    print()

    # Summary
    print("=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"Session average: {sum(session_times)/len(session_times):.3f}s")
    print(f"No-session average: {sum(no_session_times)/len(no_session_times):.3f}s")
    print(f"Internal endpoint: {internal_time:.3f}s")
    print(f"External endpoint: {external_time:.3f}s")

if __name__ == "__main__":
    main()
