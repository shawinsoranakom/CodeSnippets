async def test_multiple_sessions_simultaneous(srv):
    """3 independent sessions open at the same time, each navigating
    different pages. They should not interfere."""
    cfg = BrowserConfig(headless=True, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        sessions = [
            CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS, session_id=f"sess_{j}", verbose=False,
            )
            for j in range(3)
        ]

        # Step 1: open all sessions
        for j, s in enumerate(sessions):
            r = await c.arun(url=_u(srv, j * 10), config=s)
            assert r.success, f"Session {j} open failed"

        assert len(bm.sessions) == 3

        # Step 2: navigate each session to a second page
        for j, s in enumerate(sessions):
            r = await c.arun(url=_u(srv, j * 10 + 1), config=s)
            assert r.success, f"Session {j} step 2 failed"

        # Step 3: kill sessions one by one, verify others unaffected
        await c.crawler_strategy.kill_session("sess_0")
        assert "sess_0" not in bm.sessions
        assert "sess_1" in bm.sessions
        assert "sess_2" in bm.sessions

        # Remaining sessions still work
        r = await c.arun(url=_u(srv, 99), config=sessions[1])
        assert r.success