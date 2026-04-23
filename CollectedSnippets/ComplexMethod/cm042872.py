async def test_prefetch_with_deep_crawl(self):
        """Test prefetch mode with deep crawl strategy."""
        from crawl4ai import BFSDeepCrawlStrategy

        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(
                prefetch=True,
                deep_crawl_strategy=BFSDeepCrawlStrategy(
                    max_depth=1,
                    max_pages=3
                )
            )

            result_container = await crawler.arun(TEST_DOMAIN, config=config)

            # Handle both list and iterator results
            if hasattr(result_container, '__aiter__'):
                results = [r async for r in result_container]
            else:
                results = list(result_container) if hasattr(result_container, '__iter__') else [result_container]

            # Each result should have HTML and links
            for result in results:
                assert result.html is not None
                assert result.links is not None

            # Should have crawled at least one page
            assert len(results) >= 1