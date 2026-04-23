async def test_regex_output_format(local_server):
    """Verify each regex extraction result has the expected keys:
    url, label, value, span."""
    strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.Email)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url=f"{local_server}/regex-test", config=config)
        assert result.success
        extracted = json.loads(result.extracted_content)
        assert len(extracted) > 0
        for item in extracted:
            assert "url" in item, f"Missing 'url' key in {item}"
            assert "label" in item, f"Missing 'label' key in {item}"
            assert "value" in item, f"Missing 'value' key in {item}"
            assert "span" in item, f"Missing 'span' key in {item}"
            # Span should be a list/tuple of two ints
            span = item["span"]
            assert isinstance(span, (list, tuple)) and len(span) == 2