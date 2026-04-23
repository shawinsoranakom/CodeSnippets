async def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "#"*70)
    print("# PAGE REUSE RACE CONDITION FIX - INTEGRATION TESTS")
    print("#"*70)

    tests = [
        ("Single crawl works", test_single_crawl_still_works),
        ("Sequential crawls work", test_sequential_crawls_work),
        ("Concurrent crawls no race", test_concurrent_crawls_no_race_condition),
        ("High concurrency stress", test_high_concurrency_stress),
        ("Page tracking state", test_page_tracking_internal_state),
        ("Mixed sequential/concurrent", test_mixed_sequential_and_concurrent),
        ("Isolated vs shared context", test_compare_isolated_vs_shared_context),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = await test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"  EXCEPTION in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for name, p in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}")

    print("-"*70)
    print(f"  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n  ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n  {total - passed} TESTS FAILED!")
        return 1