async def test_high_concurrency_with_small_threshold(srv):
    """Stress test: 50 concurrent crawls with threshold=3."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=3,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        # 50 concurrent crawls with threshold of 3 — many version bumps
        tasks = [c.arun(url=_u(srv, i % 100), config=run) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"

        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 50