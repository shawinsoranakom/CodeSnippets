async def test_managed_concurrent_crawls(srv):
    """Concurrent crawls on managed browser — _global_pages_lock prevents
    two tasks from grabbing the same page."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(8)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"
        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 8