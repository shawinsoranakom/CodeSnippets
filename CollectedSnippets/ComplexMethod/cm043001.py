async def test_standalone_session_multistep(srv):
    """Session across 3 pages on standalone browser."""
    cfg = BrowserConfig(headless=True, verbose=False)
    sess = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, session_id="standalone_sess", verbose=False,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        for i in range(3):
            r = await c.arun(url=_u(srv, i), config=sess)
            assert r.success
            assert "standalone_sess" in bm.sessions

        # Refcount should be exactly 1
        _, page, _ = bm.sessions["standalone_sess"]
        sig = bm._page_to_sig.get(page)
        if sig:
            assert bm._context_refcounts.get(sig, 0) == 1

        # Kill session and verify cleanup
        await c.crawler_strategy.kill_session("standalone_sess")
        assert "standalone_sess" not in bm.sessions
        if sig:
            assert bm._context_refcounts.get(sig, 0) == 0