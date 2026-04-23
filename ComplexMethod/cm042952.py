async def test_avoid_css_blocks_css_requests():
    """With avoid_css=True, CSS requests must be aborted (no successful responses)."""
    browser_config = BrowserConfig(headless=True, avoid_css=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://books.toscrape.com",
            config=CrawlerRunConfig(
                cache_mode="bypass",
                capture_network_requests=True,
            ),
        )
        assert result.success
        assert result.network_requests is not None, "Network requests not captured"

        # No CSS should have gotten a successful response
        css_responses = [
            r
            for r in result.network_requests
            if r.get("event_type") == "response" and ".css" in r.get("url", "")
        ]
        assert (
            len(css_responses) == 0
        ), f"CSS responses should be blocked, but found: {[r['url'] for r in css_responses]}"

        # There SHOULD be request_failed events for CSS (proves blocking happened)
        css_failures = [
            r
            for r in result.network_requests
            if r.get("event_type") == "request_failed"
            and ".css" in r.get("url", "")
        ]
        assert (
            len(css_failures) > 0
        ), "Expected request_failed events for blocked CSS files"