async def test_full_cache_flow_docs_python(self):
        """
        Test complete cache flow with docs.python.org:
        1. Fresh crawl (slow - browser) - using BYPASS to force fresh
        2. Cache hit without validation (fast)
        3. Cache hit with validation (fast - 304)
        """
        url = "https://docs.python.org/3/"

        browser_config = BrowserConfig(headless=True, verbose=False)

        # ========== CRAWL 1: Fresh crawl (force with WRITE_ONLY to skip cache read) ==========
        config1 = CrawlerRunConfig(
            cache_mode=CacheMode.WRITE_ONLY,  # Skip reading, write new data
            check_cache_freshness=False,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            start1 = time.perf_counter()
            result1 = await crawler.arun(url, config=config1)
            time1 = time.perf_counter() - start1

        assert result1.success, f"First crawl failed: {result1.error_message}"
        # WRITE_ONLY means we did a fresh crawl and wrote to cache
        assert result1.cache_status == "miss", f"Expected 'miss', got '{result1.cache_status}'"

        print(f"\n[CRAWL 1] Fresh crawl: {time1:.2f}s (cache_status: {result1.cache_status})")

        # Verify data is stored in database
        metadata = await async_db_manager.aget_cache_metadata(url)
        assert metadata is not None, "Metadata should be stored in database"
        assert metadata.get("etag") or metadata.get("last_modified"), "Should have ETag or Last-Modified"
        print(f"  - Stored ETag: {metadata.get('etag', 'N/A')[:30]}...")
        print(f"  - Stored Last-Modified: {metadata.get('last_modified', 'N/A')}")
        print(f"  - Stored head_fingerprint: {metadata.get('head_fingerprint', 'N/A')}")
        print(f"  - Stored cached_at: {metadata.get('cached_at', 'N/A')}")

        # ========== CRAWL 2: Cache hit WITHOUT validation ==========
        config2 = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            check_cache_freshness=False,  # Skip validation - pure cache hit
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            start2 = time.perf_counter()
            result2 = await crawler.arun(url, config=config2)
            time2 = time.perf_counter() - start2

        assert result2.success, f"Second crawl failed: {result2.error_message}"
        assert result2.cache_status == "hit", f"Expected 'hit', got '{result2.cache_status}'"

        print(f"\n[CRAWL 2] Cache hit (no validation): {time2:.2f}s (cache_status: {result2.cache_status})")
        print(f"  - Speedup: {time1/time2:.1f}x faster than fresh crawl")

        # Should be MUCH faster - no browser, no HTTP request
        assert time2 < time1 / 2, f"Cache hit should be at least 2x faster (was {time1/time2:.1f}x)"

        # ========== CRAWL 3: Cache hit WITH validation (304) ==========
        config3 = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            check_cache_freshness=True,  # Validate cache freshness
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            start3 = time.perf_counter()
            result3 = await crawler.arun(url, config=config3)
            time3 = time.perf_counter() - start3

        assert result3.success, f"Third crawl failed: {result3.error_message}"
        # Should be "hit_validated" (304) or "hit_fallback" (error during validation)
        assert result3.cache_status in ["hit_validated", "hit_fallback"], \
            f"Expected validated cache hit, got '{result3.cache_status}'"

        print(f"\n[CRAWL 3] Cache hit (with validation): {time3:.2f}s (cache_status: {result3.cache_status})")
        print(f"  - Speedup: {time1/time3:.1f}x faster than fresh crawl")

        # Should still be fast - just a HEAD request, no browser
        assert time3 < time1 / 2, f"Validated cache hit should be faster than fresh crawl"

        # ========== SUMMARY ==========
        print(f"\n{'='*60}")
        print(f"PERFORMANCE SUMMARY for {url}")
        print(f"{'='*60}")
        print(f"  Fresh crawl (browser):        {time1:.2f}s")
        print(f"  Cache hit (no validation):    {time2:.2f}s ({time1/time2:.1f}x faster)")
        print(f"  Cache hit (with validation):  {time3:.2f}s ({time1/time3:.1f}x faster)")
        print(f"{'='*60}")