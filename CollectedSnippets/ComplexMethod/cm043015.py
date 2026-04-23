async def test_recycle_blocked_by_active_session(test_server):
    """An active session holds a context refcount, so the browser should NOT
    recycle while the session is open — even if pages_served >= threshold.
    This proves recycling is safe around sessions."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=3,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)
        run_no_session = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

        # Crawl 2 non-session pages (released immediately)
        for i in range(2):
            r = await crawler.arun(url=_url(test_server, i), config=run_no_session)
            assert r.success

        # Create a named session on page 3 — hits the threshold
        run_with_session = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="test_session",
            verbose=False,
        )
        r = await crawler.arun(url=_url(test_server, 2), config=run_with_session)
        assert r.success
        assert "test_session" in bm.sessions

        # We've hit 3 pages (the threshold), but the session holds a refcount
        # so recycle must NOT fire
        assert bm._pages_served == 3
        assert not bm._recycling, (
            "Recycle should not fire while a session holds a refcount"
        )

        # Browser should still be alive — use the session again
        r = await crawler.arun(url=_url(test_server, 50), config=run_with_session)
        assert r.success, "Session should still work even past recycle threshold"

        # Session reuses the same page, so counter stays at 3
        # (only get_page increments it, and session reuse skips get_page)
        assert bm._pages_served >= 3
        assert not bm._recycling