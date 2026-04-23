async def test_mhtml_capture_on_js_page_when_enabled():
    """
    Verify MHTML capture works on a page requiring JavaScript execution.
    """
    # Create a fresh browser config and crawler instance for this test
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(
        capture_mhtml=True,
        # Add a small wait or JS execution if needed for the JS page to fully render
        # For quotes.toscrape.com/js/, it renders quickly, but a wait might be safer
        # wait_for_timeout=2000 # Example: wait up to 2 seconds
        js_code="await new Promise(r => setTimeout(r, 500));" # Small delay after potential load
    )

    # Create a fresh crawler instance
    crawler = AsyncWebCrawler(config=browser_config)

    try:
        # Start the browser
        await crawler.start()
        result: CrawlResult = await crawler.arun(TEST_URL_JS, config=run_config)

        assert result is not None
        assert result.success is True, f"Crawling {TEST_URL_JS} should succeed. Error: {result.error_message}"
        assert hasattr(result, 'mhtml'), "CrawlResult object must have an 'mhtml' attribute"
        assert result.mhtml is not None, "MHTML content should be captured on JS page when enabled"
        assert isinstance(result.mhtml, str), "MHTML content should be a string"
        assert len(result.mhtml) > 500, "MHTML content from JS page seems too short"

        # Check for MHTML structure
        assert re.search(r"Content-Type: multipart/related;", result.mhtml, re.IGNORECASE)
        assert re.search(r"Content-Type: text/html", result.mhtml, re.IGNORECASE)

        # Check for content rendered by JS within the MHTML
        assert EXPECTED_CONTENT_JS in result.mhtml, \
            f"Expected JS-rendered content '{EXPECTED_CONTENT_JS}' not found within the captured MHTML"

        # Check standard HTML too
        assert result.html is not None
        assert EXPECTED_CONTENT_JS in result.html, \
             f"Expected JS-rendered content '{EXPECTED_CONTENT_JS}' not found within the standard HTML"

    finally:
        # Important: Ensure browser is completely closed even if assertions fail
        await crawler.close()
        # Help the garbage collector clean up
        crawler = None