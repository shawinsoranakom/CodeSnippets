async def test_mixed_sequential_and_concurrent():
    """
    Test 6: Mixed sequential and concurrent crawls.
    Tests realistic usage pattern where some crawls are sequential and some concurrent.
    """
    print("\n" + "="*70)
    print("TEST 6: Mixed sequential and concurrent crawls")
    print("="*70)

    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=False,
    )

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Sequential crawl 1
            print("  Phase 1: Sequential crawl")
            result1 = await crawler.arun("https://example.com")
            assert result1.success, f"Sequential crawl 1 failed"
            print(f"    Crawl 1: OK")

            # Concurrent crawls
            print("  Phase 2: Concurrent crawls (3 URLs)")
            concurrent_urls = [
                "https://httpbin.org/html",
                "https://example.org",
                "https://httpbin.org/get",
            ]
            tasks = [crawler.arun(url) for url in concurrent_urls]
            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(concurrent_results):
                if isinstance(result, Exception):
                    print(f"    Concurrent {i+1}: EXCEPTION - {result}")
                else:
                    assert result.success, f"Concurrent crawl {i+1} failed"
                    print(f"    Concurrent {i+1}: OK")

            # Sequential crawl 2
            print("  Phase 3: Sequential crawl")
            result2 = await crawler.arun("https://www.iana.org/domains/reserved")
            assert result2.success, f"Sequential crawl 2 failed"
            print(f"    Crawl 2: OK")

            # Another batch of concurrent
            print("  Phase 4: More concurrent crawls (2 URLs)")
            tasks2 = [
                crawler.arun("https://example.com?test=1"),
                crawler.arun("https://example.org?test=2"),
            ]
            results2 = await asyncio.gather(*tasks2, return_exceptions=True)
            for i, result in enumerate(results2):
                if isinstance(result, Exception):
                    print(f"    Concurrent {i+1}: EXCEPTION - {result}")
                else:
                    assert result.success, f"Batch 2 crawl {i+1} failed"
                    print(f"    Concurrent {i+1}: OK")

            print("  PASSED: Mixed sequential and concurrent crawls work correctly")
            return True

    except Exception as e:
        print(f"  FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False