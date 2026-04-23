async def test_session_lifecycle_across_recycle(test_server):
    """Full lifecycle: create session → use it → kill it → recycle fires →
    create new session → use it. End-to-end proof that recycling is safe."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=4,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)
        no_session = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

        # Phase 1: create and use a session
        sess_v1 = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="lifecycle_sess", verbose=False,
        )
        r = await crawler.arun(url=f"{test_server}/login", config=sess_v1)
        assert r.success

        r = await crawler.arun(url=f"{test_server}/dashboard", config=sess_v1)
        assert r.success
        assert "Welcome, authenticated user" in r.html

        # Phase 2: kill session
        await crawler.crawler_strategy.kill_session("lifecycle_sess")

        # Phase 3: push past threshold with non-session crawls
        for i in range(5):
            r = await crawler.arun(url=_url(test_server, i), config=no_session)
            assert r.success

        await asyncio.sleep(0.5)

        # Recycle should have happened (session killed, refcount=0)
        assert bm._pages_served < 6, (
            f"Expected reset after recycle, got {bm._pages_served}"
        )

        # Phase 4: new session on the fresh browser
        sess_v2 = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="lifecycle_sess_v2", verbose=False,
        )
        r = await crawler.arun(url=f"{test_server}/login", config=sess_v2)
        assert r.success
        assert "lifecycle_sess_v2" in bm.sessions

        r = await crawler.arun(url=f"{test_server}/dashboard", config=sess_v2)
        assert r.success
        assert "Welcome, authenticated user" in r.html, (
            "New session after recycle should work with cookies"
        )