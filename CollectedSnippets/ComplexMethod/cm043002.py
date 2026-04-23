async def test_standalone_recycle_with_concurrent_crawls(srv):
    """15 concurrent crawls straddling a recycle boundary on standalone."""
    cfg = BrowserConfig(
        headless=True, verbose=False, max_pages_before_recycle=5,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(15)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"
        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 15