async def test_prefetch_links_structure(self):
        """Test that links have the expected structure."""
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(prefetch=True)
            result = await crawler.arun(TEST_DOMAIN, config=config)

            assert result.links is not None

            # Check internal links structure
            if result.links["internal"]:
                link = result.links["internal"][0]
                assert "href" in link
                assert "text" in link
                assert link["href"].startswith("http")

            # Check external links structure (if any)
            if result.links["external"]:
                link = result.links["external"][0]
                assert "href" in link
                assert "text" in link
                assert link["href"].startswith("http")