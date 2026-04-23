async def test_concurrent_crawls_dont_block_on_recycle(srv):
    """Concurrent crawls should not block — old browser drains while new one serves."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=5,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        # Launch 20 concurrent crawls
        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed — no blocking, no errors
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"

        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 20, f"Only {len(successes)} succeeded"

        # Version should have bumped multiple times
        assert bm._browser_version >= 2, "Should have recycled at least once"