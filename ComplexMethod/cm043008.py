async def test_managed_isolated_session_recycle_concurrent(srv):
    """The ultimate stress test: managed browser + isolated contexts +
    sessions + recycle + concurrent crawls.

    Flow:
    1. Open session A
    2. Fire 8 concurrent non-session crawls (threshold=5, but session blocks)
    3. Kill session A
    4. Fire 3 more non-session crawls to trigger recycle
    5. Open session B on the fresh browser
    6. Verify session B works
    """
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        create_isolated_context=True,
        max_pages_before_recycle=5,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)
        no_sess = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

        # Step 1: open session
        sess_a = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="ultimate_a", verbose=False,
        )
        r = await c.arun(url=f"{srv}/login", config=sess_a)
        assert r.success

        # Step 2: concurrent non-session crawls
        tasks = [c.arun(url=_u(srv, i), config=no_sess) for i in range(8)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions in step 2: {excs[:3]}"

        # Session blocks recycle
        assert "ultimate_a" in bm.sessions

        # Step 3: kill session
        await c.crawler_strategy.kill_session("ultimate_a")

        # Step 4: trigger recycle
        for i in range(3):
            r = await c.arun(url=_u(srv, 80 + i), config=no_sess)
            assert r.success

        await asyncio.sleep(0.5)

        # Step 5: new session on fresh browser
        sess_b = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="ultimate_b", verbose=False,
        )
        r = await c.arun(url=f"{srv}/login", config=sess_b)
        assert r.success
        assert "ultimate_b" in bm.sessions

        # Step 6: verify it works
        r = await c.arun(url=f"{srv}/dashboard", config=sess_b)
        assert r.success