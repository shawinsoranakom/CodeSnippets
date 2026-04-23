async def test_session_refcount_stays_at_one(test_server):
    """Verify that a session holds exactly 1 refcount throughout its
    lifecycle, regardless of how many times it's reused."""
    config = BrowserConfig(headless=True, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        session_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="refcount_test", verbose=False,
        )

        # Create session
        r = await crawler.arun(url=f"{test_server}/step1", config=session_cfg)
        assert r.success

        # Find the session's context signature
        _, page, _ = bm.sessions["refcount_test"]
        sig = bm._page_to_sig.get(page)
        if sig:
            refcount = bm._context_refcounts.get(sig, 0)
            assert refcount == 1, (
                f"Session should hold exactly 1 refcount, got {refcount}"
            )

        # Reuse session multiple times — refcount should stay at 1
        for url in ["/step2", "/step3", "/dashboard"]:
            r = await crawler.arun(url=f"{test_server}{url}", config=session_cfg)
            assert r.success

            if sig:
                refcount = bm._context_refcounts.get(sig, 0)
                assert refcount == 1, (
                    f"After reuse, refcount should still be 1, got {refcount}"
                )

        # Kill session — refcount should drop to 0
        await crawler.crawler_strategy.kill_session("refcount_test")
        if sig:
            refcount = bm._context_refcounts.get(sig, 0)
            assert refcount == 0, (
                f"After kill, refcount should be 0, got {refcount}"
            )