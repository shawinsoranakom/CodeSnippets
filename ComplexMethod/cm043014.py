async def test_concurrent_crawls_across_recycle(test_server):
    """Launch concurrent crawls that straddle the recycle threshold.
    Recycling should wait for in-flight crawls to finish, not crash them."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=5,
    )
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        # Fire 10 concurrent crawls with threshold=5
        urls = [_url(test_server, i) for i in range(10)]
        tasks = [crawler.arun(url=u, config=run_config) for u in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, (
            f"Got {len(exceptions)} exceptions during concurrent recycle: "
            f"{exceptions[:3]}"
        )
        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 10, (
            f"Only {len(successes)}/10 crawls succeeded"
        )