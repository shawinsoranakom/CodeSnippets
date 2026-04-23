async def test_version_bump_on_threshold(srv):
    """Browser version should bump when threshold is reached."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=3,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        assert bm._browser_version == 1

        # Crawl 2 pages — no bump yet
        for i in range(2):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success

        assert bm._browser_version == 1, "Version should still be 1 after 2 pages"
        assert bm._pages_served == 2

        # 3rd page hits threshold (3) and triggers bump AFTER the page is served
        r = await c.arun(url=_u(srv, 2), config=run)
        assert r.success
        assert bm._browser_version == 2, "Version should bump after 3rd page"
        assert bm._pages_served == 0, "Counter resets after bump"

        # 4th page is first page of version 2
        r = await c.arun(url=_u(srv, 3), config=run)
        assert r.success
        assert bm._pages_served == 1