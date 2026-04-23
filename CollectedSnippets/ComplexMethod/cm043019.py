async def test_two_concurrent_sessions_block_recycle(test_server):
    """Two sessions open at the same time, with non-session crawls interleaved.
    Both sessions should prevent recycle and remain functional."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=3,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        session_a = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="sess_a", verbose=False,
        )
        session_b = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="sess_b", verbose=False,
        )
        no_session = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

        # Open session A
        r = await crawler.arun(url=f"{test_server}/login", config=session_a)
        assert r.success

        # Open session B
        r = await crawler.arun(url=f"{test_server}/step1", config=session_b)
        assert r.success

        # 5 non-session crawls — pages_served goes to 7 (2 sessions + 5)
        for i in range(5):
            r = await crawler.arun(url=_url(test_server, i), config=no_session)
            assert r.success

        # Both sessions hold refcounts → recycle blocked
        assert not bm._recycling
        assert "sess_a" in bm.sessions
        assert "sess_b" in bm.sessions

        # Both sessions still work
        r = await crawler.arun(url=f"{test_server}/dashboard", config=session_a)
        assert r.success
        assert "Welcome, authenticated user" in r.html

        r = await crawler.arun(url=f"{test_server}/step2", config=session_b)
        assert r.success
        assert "Step 2" in r.html