async def test_comprehensive_crawl():
    """
    Run a comprehensive crawl to verify overall stability with new features.
    """
    print_test("Comprehensive Crawl Test", "Overall")

    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

        async with AsyncWebCrawler(config=BrowserConfig(headless=True), verbose=False) as crawler:
            result = await crawler.arun(
                url="https://httpbin.org/html",
                config=CrawlerRunConfig()
            )

        checks = []

        if result.success:
            checks.append("success=True")
        else:
            record_result("Comprehensive Crawl", "Overall", False,
                         f"Crawl failed: {result.error_message}")
            return

        if result.html and len(result.html) > 100:
            checks.append(f"html={len(result.html)} chars")

        if result.markdown and result.markdown.raw_markdown:
            checks.append(f"markdown={len(result.markdown.raw_markdown)} chars")

        if result.links:
            total_links = len(result.links.get("internal", [])) + len(result.links.get("external", []))
            checks.append(f"links={total_links}")

        record_result("Comprehensive Crawl", "Overall", True,
                     f"All checks passed: {', '.join(checks)}")

    except Exception as e:
        record_result("Comprehensive Crawl", "Overall", False, f"Exception: {e}")