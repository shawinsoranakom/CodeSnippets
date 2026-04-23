async def test_recycle_concurrent_sessions_and_nonsessions(srv):
    """Open 2 sessions + fire 10 non-session crawls concurrently with
    recycle threshold=5. Sessions should block recycle until they're
    done or killed. All crawls should succeed."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=5,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        # Open sessions first
        sess_a = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="stress_a", verbose=False,
        )
        sess_b = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="stress_b", verbose=False,
        )
        r = await c.arun(url=f"{srv}/login", config=sess_a)
        assert r.success
        r = await c.arun(url=f"{srv}/login", config=sess_b)
        assert r.success

        # Fire 10 concurrent non-session crawls
        no_sess = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        tasks = [c.arun(url=_u(srv, i), config=no_sess) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"

        # Sessions should still be alive (blocking recycle)
        assert "stress_a" in bm.sessions
        assert "stress_b" in bm.sessions

        # Use sessions again — should work
        r = await c.arun(url=f"{srv}/dashboard", config=sess_a)
        assert r.success
        r = await c.arun(url=f"{srv}/dashboard", config=sess_b)
        assert r.success