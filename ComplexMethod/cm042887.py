async def test_parallel_start_race(self):
        """Multiple crawlers calling start() simultaneously — lock prevents races."""
        cfg = BrowserConfig(
            cdp_url=CDP_URL,
            headless=True,
            cache_cdp_connection=True,
        )

        crawlers = [AsyncWebCrawler(config=cfg) for _ in range(5)]

        # Start all at once — this hammers _CDPConnectionCache.acquire() concurrently
        await asyncio.gather(*[c.start() for c in crawlers])

        # All should have the same browser reference
        browsers = set()
        for c in crawlers:
            bm = c.crawler_strategy.browser_manager
            browsers.add(id(bm.browser))

        # With caching, they should all share the same browser object
        assert len(browsers) == 1, f"Expected 1 shared browser, got {len(browsers)}"

        # Ref count should be 5
        _, _, count = _CDPConnectionCache._cache[CDP_URL]
        assert count == 5

        # Close all
        await asyncio.gather(*[c.close() for c in crawlers])

        # Cache should be empty
        assert CDP_URL not in _CDPConnectionCache._cache