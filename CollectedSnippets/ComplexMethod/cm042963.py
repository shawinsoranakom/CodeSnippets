async def test_high_concurrency_stress():
    """
    Test 4: High concurrency stress test - many concurrent crawls.
    This stresses the page tracking system to ensure it handles many concurrent operations.
    """
    print("\n" + "="*70)
    print("TEST 4: High concurrency stress test (10 concurrent crawls)")
    print("="*70)

    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=False,
    )

    # Generate multiple unique URLs
    base_urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://example.org",
        "https://httpbin.org/get",
        "https://www.iana.org/domains/reserved",
    ]

    # Create 10 URLs by adding query params
    urls = []
    for i in range(10):
        url = f"{base_urls[i % len(base_urls)]}?test={i}&t={int(time.time())}"
        urls.append(url)

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print(f"  Launching {len(urls)} concurrent crawls...")
            start_time = time.time()

            # Launch all crawls concurrently
            tasks = [crawler.arun(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            elapsed = time.time() - start_time
            print(f"  Completed in {elapsed:.2f}s")

            # Count results
            success_count = 0
            error_count = 0
            exception_count = 0

            for url, result in zip(urls, results):
                if isinstance(result, Exception):
                    exception_count += 1
                elif result.success:
                    success_count += 1
                else:
                    error_count += 1

            print(f"  Results: {success_count} success, {error_count} errors, {exception_count} exceptions")

            # At least 80% should succeed (allowing for some network issues)
            min_success = int(len(urls) * 0.8)
            assert success_count >= min_success, f"Only {success_count}/{len(urls)} succeeded (min: {min_success})"

            print(f"  PASSED: High concurrency test ({success_count}/{len(urls)} succeeded)")
            return True

    except Exception as e:
        print(f"  FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False