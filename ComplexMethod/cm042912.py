async def test_images_scoring(local_server):
    """High-quality images (large, with alt text) should score higher
    than small icons without alt text."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/images-page", config=CrawlerRunConfig())
        assert result.success
        images = result.media.get("images", [])
        assert len(images) >= 2

        # Find the hero/landscape image and the small icon
        hero = None
        icon = None
        for img in images:
            src = img.get("src", "")
            if "landscape" in src or "hero" in src:
                hero = img
            elif "icon" in src and img.get("alt", "") == "":
                icon = img

        if hero and icon:
            assert hero["score"] > icon["score"], (
                f"Hero score ({hero['score']}) should exceed icon score ({icon['score']})"
            )