async def test_rapid_recycle_concurrent(srv):
    """Recycle threshold=3 with 12 concurrent crawls. Concurrency +
    rapid recycling together."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=3,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(12)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"
        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 12