async def test_session_survives_threshold_with_interleaved_crawls(test_server):
    """Open a session, then do many non-session crawls that push
    pages_served past the recycle threshold. The session should prevent
    recycle from firing (refcount > 0). Then continue using the session
    and it should still work."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=5,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        # Start a session — step 1
        session_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="persistent_session",
            verbose=False,
        )
        r = await crawler.arun(url=f"{test_server}/login", config=session_cfg)
        assert r.success
        assert "persistent_session" in bm.sessions

        # Fire 8 non-session crawls — pushes pages_served to 9
        # (1 from session + 8 = 9, well past threshold of 5)
        no_session = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        for i in range(8):
            r = await crawler.arun(url=_url(test_server, i), config=no_session)
            assert r.success, f"Non-session crawl {i} failed"

        # Recycle should NOT have fired — session holds refcount
        assert bm._pages_served == 9, (
            f"Expected 9 pages served, got {bm._pages_served}"
        )
        assert not bm._recycling
        assert "persistent_session" in bm.sessions, (
            "Session should still exist — recycle blocked by refcount"
        )

        # Session should still work — navigate to dashboard with cookies
        r = await crawler.arun(url=f"{test_server}/dashboard", config=session_cfg)
        assert r.success
        assert "Welcome, authenticated user" in r.html, (
            "Session cookies should still work after interleaved non-session crawls"
        )