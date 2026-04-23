async def test_prefetch_returns_html_and_links(self):
        """Test that prefetch mode returns HTML and links only."""
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(prefetch=True)
            result = await crawler.arun(TEST_DOMAIN, config=config)

            # Should have HTML
            assert result.html is not None
            assert len(result.html) > 0
            assert "<html" in result.html.lower() or "<!doctype" in result.html.lower()

            # Should have links
            assert result.links is not None
            assert "internal" in result.links
            assert "external" in result.links

            # Should NOT have processed content
            assert result.markdown is None or (
                hasattr(result.markdown, 'raw_markdown') and
                result.markdown.raw_markdown is None
            )
            assert result.cleaned_html is None
            assert result.extracted_content is None