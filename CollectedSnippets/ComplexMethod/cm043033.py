async def test_verify_ip_consistency(self):
        """Verify that sticky session actually uses same IP.

        This test requires real proxies set in environment variables:
        TEST_PROXY_1=ip:port:user:pass
        TEST_PROXY_2=ip:port:user:pass
        """
        import re

        # Load proxies from environment
        proxy_strs = [
            os.environ.get('TEST_PROXY_1', ''),
            os.environ.get('TEST_PROXY_2', '')
        ]
        proxies = [ProxyConfig.from_string(p) for p in proxy_strs if p]

        if len(proxies) < 2:
            pytest.skip("Need at least 2 proxies for this test")

        strategy = RoundRobinProxyStrategy(proxies)

        # Config WITH sticky session
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            proxy_rotation_strategy=strategy,
            proxy_session_id="ip-verify-session",
            page_timeout=30000
        )

        browser_config = BrowserConfig(headless=True)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            ips = []

            for i in range(3):
                result = await crawler.arun(
                    url="https://httpbin.org/ip",
                    config=config
                )

                if result and result.success and result.html:
                    # Extract IP from response
                    ip_match = re.search(r'"origin":\s*"([^"]+)"', result.html)
                    if ip_match:
                        ips.append(ip_match.group(1))

            await strategy.release_session("ip-verify-session")

            # All IPs should be same for sticky session
            if len(ips) >= 2:
                assert len(set(ips)) == 1, f"Expected same IP, got: {ips}"