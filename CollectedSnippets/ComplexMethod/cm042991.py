async def test_mhtml_capture_when_enabled():
    """
    Verify that when CrawlerRunConfig has capture_mhtml=True,
    the CrawlResult contains valid MHTML content.
    """
    # Create a fresh browser config and crawler instance for this test
    browser_config = BrowserConfig(headless=True) # Use headless for testing CI/CD
    # --- Key: Enable MHTML capture in the run config ---
    run_config = CrawlerRunConfig(capture_mhtml=True)

    # Create a fresh crawler instance
    crawler = AsyncWebCrawler(config=browser_config)

    try:
        # Start the browser
        await crawler.start()

        # Perform the crawl with the MHTML-enabled config
        result: CrawlResult = await crawler.arun(TEST_URL_SIMPLE, config=run_config)

        # --- Assertions ---
        assert result is not None, "Crawler should return a result object"
        assert result.success is True, f"Crawling {TEST_URL_SIMPLE} should succeed. Error: {result.error_message}"

        # 1. Check if the mhtml attribute exists (will fail if CrawlResult not updated)
        assert hasattr(result, 'mhtml'), "CrawlResult object must have an 'mhtml' attribute"

        # 2. Check if mhtml is populated
        assert result.mhtml is not None, "MHTML content should be captured when enabled"
        assert isinstance(result.mhtml, str), "MHTML content should be a string"
        assert len(result.mhtml) > 500, "MHTML content seems too short, likely invalid" # Basic sanity check

        # 3. Check for MHTML structure indicators (more robust than simple string contains)
        # MHTML files are multipart MIME messages
        assert re.search(r"Content-Type: multipart/related;", result.mhtml, re.IGNORECASE), \
            "MHTML should contain 'Content-Type: multipart/related;'"
        # Should contain a boundary definition
        assert re.search(r"boundary=\"----MultipartBoundary", result.mhtml), \
            "MHTML should contain a multipart boundary"
        # Should contain the main HTML part
        assert re.search(r"Content-Type: text/html", result.mhtml, re.IGNORECASE), \
            "MHTML should contain a 'Content-Type: text/html' part"

        # 4. Check if the *actual page content* is within the MHTML string
        # This confirms the snapshot captured the rendered page
        assert EXPECTED_CONTENT_SIMPLE in result.mhtml, \
            f"Expected content '{EXPECTED_CONTENT_SIMPLE}' not found within the captured MHTML"

        # 5. Ensure standard HTML is still present and correct
        assert result.html is not None, "Standard HTML should still be present"
        assert isinstance(result.html, str), "Standard HTML should be a string"
        assert EXPECTED_CONTENT_SIMPLE in result.html, \
            f"Expected content '{EXPECTED_CONTENT_SIMPLE}' not found within the standard HTML"

    finally:
        # Important: Ensure browser is completely closed even if assertions fail
        await crawler.close()
        # Help the garbage collector clean up
        crawler = None