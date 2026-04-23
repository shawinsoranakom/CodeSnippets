async def test_compare_isolated_vs_shared_context():
    """
    Test 7: Compare behavior between isolated and shared context modes.
    Both should work for concurrent crawls now.
    """
    print("\n" + "="*70)
    print("TEST 7: Compare isolated vs shared context modes")
    print("="*70)

    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://example.org",
    ]

    # Test with create_isolated_context=True
    print("  Testing with create_isolated_context=True:")
    browser_config_isolated = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=True,
    )

    try:
        async with AsyncWebCrawler(config=browser_config_isolated) as crawler:
            tasks = [crawler.arun(url) for url in urls]
            results_isolated = await asyncio.gather(*tasks, return_exceptions=True)

            isolated_success = sum(1 for r in results_isolated if not isinstance(r, Exception) and r.success)
            print(f"    Isolated context: {isolated_success}/{len(urls)} succeeded")
    except Exception as e:
        print(f"    Isolated context: FAILED - {e}")
        isolated_success = 0

    # Test with create_isolated_context=False
    print("  Testing with create_isolated_context=False:")
    browser_config_shared = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=False,
    )

    try:
        async with AsyncWebCrawler(config=browser_config_shared) as crawler:
            tasks = [crawler.arun(url) for url in urls]
            results_shared = await asyncio.gather(*tasks, return_exceptions=True)

            shared_success = sum(1 for r in results_shared if not isinstance(r, Exception) and r.success)
            print(f"    Shared context: {shared_success}/{len(urls)} succeeded")
    except Exception as e:
        print(f"    Shared context: FAILED - {e}")
        shared_success = 0

    # Both modes should work
    assert isolated_success == len(urls), f"Isolated context: only {isolated_success}/{len(urls)} succeeded"
    assert shared_success == len(urls), f"Shared context: only {shared_success}/{len(urls)} succeeded"

    print("  PASSED: Both context modes work correctly for concurrent crawls")
    return True