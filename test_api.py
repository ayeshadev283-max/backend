"""
Test script for RAG Chatbot API deployed on Hugging Face Spaces
"""
import requests
import json
import time
from typing import Dict, Any


API_BASE_URL = "https://ayeshassdev-aibook.hf.space"


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_json(data: Dict[str, Any], indent: int = 2):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=indent))


def test_health() -> bool:
    """Test the health endpoint"""
    print_section("TEST 1: Health Check")

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_json(data)

            # Check service status
            status = data.get('status', 'unknown')
            services = data.get('services', {})

            print(f"\nOverall Status: {status.upper()}")
            print("\nService Health:")
            for service, health in services.items():
                mark = "[OK]" if health == "healthy" else "[!!]"
                print(f"  {mark} {service}: {health}")

            return status in ['healthy', 'degraded']
        else:
            print(f"[ERROR] Health check failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False


def test_root() -> bool:
    """Test the root endpoint"""
    print_section("TEST 2: Root Endpoint")

    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_json(data)
            print(f"\n[OK] API Name: {data.get('name', 'Unknown')}")
            print(f"[OK] Version: {data.get('version', 'Unknown')}")
            return True
        else:
            print(f"[ERROR] Root endpoint failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False


def test_query(query: str, book_id: str = "physical-ai-robotics", chapter: int = None) -> Dict[str, Any]:
    """Test the query endpoint"""
    print_section(f"TEST 3: Query - '{query}'")

    payload = {
        "query": query,
        "book_context": {
            "book_id": book_id
        }
    }

    # Add optional fields if provided
    if chapter:
        payload["book_context"]["chapter_number"] = chapter

    print(f"Request Payload:")
    print_json(payload)

    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/v1/query",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        duration = (time.time() - start_time) * 1000  # Convert to ms

        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Time: {duration:.0f}ms")

        if response.status_code == 200:
            data = response.json()
            print("\n[SUCCESS] Query successful!")
            print("\nResponse:")
            print_json(data)

            # Extract key information
            if 'answer' in data:
                print(f"\nAnswer Preview:")
                answer = data['answer']
                preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"  {preview}")

            if 'sources' in data:
                print(f"\nSources Retrieved: {len(data['sources'])}")
                for i, source in enumerate(data['sources'][:3], 1):
                    score = source.get('similarity_score', 'N/A')
                    print(f"  {i}. Similarity: {score}")

            return data
        else:
            print(f"\n[ERROR] Query failed with status {response.status_code}")
            try:
                error_data = response.json()
                print("\nError Response:")
                print_json(error_data)
            except:
                print(f"Response: {response.text}")
            return {}

    except requests.Timeout:
        print("\n[ERROR] Request timed out (>30 seconds)")
        return {}
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        return {}


def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*70)
    print("  RAG CHATBOT API TEST SUITE")
    print("  API: https://ayeshassdev-aibook.hf.space")
    print("="*70)

    results = {
        'health': False,
        'root': False,
        'query': False
    }

    # Test 1: Health Check
    results['health'] = test_health()
    time.sleep(1)

    # Test 2: Root Endpoint
    results['root'] = test_root()
    time.sleep(1)

    # Test 3: Query Endpoint - Multiple queries
    sample_queries = [
        "What is machine learning?",
        "Explain artificial intelligence",
        "What is deep learning?",
    ]

    for query in sample_queries:
        response = test_query(query, book_id="physical-ai-robotics")
        if response:
            results['query'] = True
        time.sleep(2)  # Rate limiting

    # Summary
    print_section("TEST SUMMARY")
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    print(f"\nTests Passed: {passed_tests}/{total_tests}")
    print("\nDetailed Results:")
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {test_name.replace('_', ' ').title()}")

    if passed_tests == total_tests:
        print("\n*** All tests passed! ***")
    elif passed_tests > 0:
        print("\n*** Some tests passed, but there are issues to fix ***")
    else:
        print("\n*** All tests failed - check API deployment ***")

    print("\n" + "="*70)


if __name__ == "__main__":
    run_all_tests()
