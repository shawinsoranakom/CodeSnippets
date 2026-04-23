async def main():
    """Run all tests."""
    print("\n🧪 TESTING COMPLETE FIX FOR DOCKER FILTER AND JSON ISSUES")
    print("=" * 60)
    print("Make sure the server is running with the updated code!")
    print("=" * 60)

    results = []

    # Test 1: Docker client
    max_pages_ = [20, 5]
    timeouts = [30, 60]
    filter_chain_test_cases = [
        [
            URLPatternFilter(
                # patterns=["*about*", "*privacy*", "*terms*"],
                patterns=["*advanced*"],
                reverse=True
            ),
        ],
        [
            ContentRelevanceFilter(
                query="about faq",
                threshold=0.2,
            ),
        ],
    ]
    for idx, (filter_chain, max_pages, timeout) in enumerate(zip(filter_chain_test_cases, max_pages_, timeouts)):
        docker_passed = await test_with_docker_client(filter_chain=filter_chain, max_pages=max_pages, timeout=timeout)
        results.append((f"Docker Client w/ filter chain {idx}", docker_passed))

    # Test 2: REST API
    max_pages_ = [20, 5, 5]
    timeouts = [30, 60, 60]
    filters_test_cases = [
        [
            {
                "type": "URLPatternFilter",
                "params": {
                    "patterns": ["*advanced*"],
                    "reverse": True
                }
            }
        ],
        [
            {
                "type": "ContentRelevanceFilter",
                "params": {
                    "query": "about faq",
                    "threshold": 0.2,
                }
            }
        ],
        [
            {
                "type": "ContentRelevanceFilter",
                "params": {
                    "query": ["about", "faq"],
                    "threshold": 0.2,
                }
            }
        ],
    ]
    for idx, (filters, max_pages, timeout) in enumerate(zip(filters_test_cases, max_pages_, timeouts)):
        rest_passed = await test_with_rest_api(filters=filters, max_pages=max_pages, timeout=timeout)
        results.append((f"REST API w/ filters {idx}", rest_passed))

    # Summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ Some tests failed. Please check the server logs for details.")

    return 0 if all_passed else 1