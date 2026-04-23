async def test_avoid_css_with_text_mode_combines():
    """Both avoid_css and text_mode should combine their blocking rules."""
    browser_config = BrowserConfig(
        headless=True, avoid_css=True, text_mode=True
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://books.toscrape.com",
            config=CrawlerRunConfig(
                cache_mode="bypass",
                capture_network_requests=True,
            ),
        )
        assert result.success
        assert result.network_requests is not None

        successful = [
            r for r in result.network_requests if r.get("event_type") == "response"
        ]

        # CSS should be blocked (via avoid_css)
        css_hits = [r for r in successful if ".css" in r.get("url", "")]
        assert len(css_hits) == 0, "CSS should be blocked by avoid_css"

        # Images should be blocked (via text_mode)
        img_exts = (".jpg", ".jpeg", ".png", ".gif", ".webp")
        img_hits = [
            r
            for r in successful
            if any(r.get("url", "").lower().endswith(ext) for ext in img_exts)
        ]
        assert len(img_hits) == 0, "Images should be blocked by text_mode"