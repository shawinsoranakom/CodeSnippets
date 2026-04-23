async def test_extract_links():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert result.success
        assert result.links
        links = result.links
        assert isinstance(links, dict)
        assert "internal" in links
        assert "external" in links
        assert isinstance(links["internal"], list)
        assert isinstance(links["external"], list)
        for link in links["internal"] + links["external"]:
            assert "href" in link
            assert "text" in link