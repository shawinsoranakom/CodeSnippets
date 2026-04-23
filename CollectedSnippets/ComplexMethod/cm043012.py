async def test_extract_media_and_links():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, bypass_cache=True)

        assert result.success
        assert result.media
        assert isinstance(result.media, dict)
        assert "images" in result.media
        assert result.links
        assert isinstance(result.links, dict)
        assert "internal" in result.links and "external" in result.links