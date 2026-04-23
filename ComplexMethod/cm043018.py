async def test_three_step_session_blocks_recycle(test_server):
    """3-step session (step1 → step2 → step3) with low threshold.
    The session's refcount should block recycle for the entire flow."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=2,  # very low threshold
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        session_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="multistep",
            verbose=False,
        )

        # Step 1
        r = await crawler.arun(url=f"{test_server}/step1", config=session_cfg)
        assert r.success
        assert "Step 1" in r.html

        # Step 2 — pages_served is still 1 (session reuse doesn't increment)
        # but even if it did, refcount blocks recycle
        r = await crawler.arun(url=f"{test_server}/step2", config=session_cfg)
        assert r.success
        assert "Step 2" in r.html

        # Step 3
        r = await crawler.arun(url=f"{test_server}/step3", config=session_cfg)
        assert r.success
        assert "Step 3" in r.html

        # Session page reuse doesn't increment counter (only get_page does)
        # Initial creation = 1 page, subsequent calls reuse it
        assert bm._pages_served == 1
        assert not bm._recycling
        assert "multistep" in bm.sessions