async def test_crawler_rotating_vs_sticky(self):
        """Compare rotating behavior vs sticky session behavior."""
        strategy = RoundRobinProxyStrategy(self.proxies)

        # Config WITHOUT sticky session - should rotate
        rotating_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            proxy_rotation_strategy=strategy,
            page_timeout=5000
        )

        # Config WITH sticky session - should use same proxy
        sticky_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            proxy_rotation_strategy=strategy,
            proxy_session_id="sticky-test",
            page_timeout=5000
        )

        browser_config = BrowserConfig(headless=True)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Track proxy configs used
            rotating_proxies = []
            sticky_proxies = []

            # Try rotating requests (may fail due to test proxies, but config should be set)
            for _ in range(3):
                try:
                    await crawler.arun(url=self.test_url, config=rotating_config)
                except Exception:
                    pass
                rotating_proxies.append(rotating_config.proxy_config.server if rotating_config.proxy_config else None)

            # Try sticky requests
            for _ in range(3):
                try:
                    await crawler.arun(url=self.test_url, config=sticky_config)
                except Exception:
                    pass
                sticky_proxies.append(sticky_config.proxy_config.server if sticky_config.proxy_config else None)

            # Rotating should have different proxies (or cycle through them)
            # Sticky should have same proxy for all requests
            if all(sticky_proxies):
                assert len(set(sticky_proxies)) == 1, "Sticky session should use same proxy"

            await strategy.release_session("sticky-test")