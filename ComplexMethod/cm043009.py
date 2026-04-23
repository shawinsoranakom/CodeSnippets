async def test_extract_media():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert result.success
        assert result.media
        media = result.media
        assert isinstance(media, dict)
        assert "images" in media
        assert isinstance(media["images"], list)
        for image in media["images"]:
            assert "src" in image
            assert "alt" in image
            assert "type" in image