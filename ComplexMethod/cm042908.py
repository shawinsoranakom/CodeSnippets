async def test_idempotent_crawl(local_server):
    """Crawl same URL twice with BYPASS cache; both should succeed with similar content."""
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result1 = await crawler.arun(local_server + "/products", config=config)
        result2 = await crawler.arun(local_server + "/products", config=config)
        assert result1.success, f"First crawl failed: {result1.error_message}"
        assert result2.success, f"Second crawl failed: {result2.error_message}"
        # Both should have similar content length (within 20% tolerance)
        len1 = len(result1.markdown or "")
        len2 = len(result2.markdown or "")
        if len1 > 0 and len2 > 0:
            ratio = min(len1, len2) / max(len1, len2)
            assert ratio > 0.8, (
                f"Idempotent crawls should produce similar content "
                f"(len1={len1}, len2={len2}, ratio={ratio:.2f})"
            )