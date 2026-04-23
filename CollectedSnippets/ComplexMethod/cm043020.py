async def test_recycle_fires_after_session_killed(test_server):
    """Session blocks recycle. After session is killed (refcount drops to 0),
    the next non-session crawl that pushes past threshold triggers recycle."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=3,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)
        no_session = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

        # Open a session (1 page)
        session_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="temp_sess", verbose=False,
        )
        r = await crawler.arun(url=f"{test_server}/step1", config=session_cfg)
        assert r.success

        # 3 non-session crawls (4 pages total, threshold=3, but session blocks)
        for i in range(3):
            r = await crawler.arun(url=_url(test_server, i), config=no_session)
            assert r.success

        pages_before_kill = bm._pages_served
        assert pages_before_kill == 4
        assert not bm._recycling

        # Kill the session — refcount drops to 0
        await crawler.crawler_strategy.kill_session("temp_sess")
        assert "temp_sess" not in bm.sessions

        # One more crawl — should trigger recycle (pages_served=5 >= 3, refcounts=0)
        r = await crawler.arun(url=_url(test_server, 99), config=no_session)
        assert r.success

        await asyncio.sleep(0.5)

        # Recycle should have fired — counter reset
        assert bm._pages_served < pages_before_kill, (
            f"Expected counter reset after recycle, got {bm._pages_served}"
        )