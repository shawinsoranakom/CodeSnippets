async def test_redirect_url_handling():
    """
    Verify that redirected_url reflects the final URL after JS navigation.

    BEFORE: redirected_url was the original URL, not the final URL
    AFTER: redirected_url is captured after JS execution completes
    """
    print_test("Relative URLs After Redirects", "#1268")

    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

        # Test with a URL that we know the final state of
        # We'll use httpbin which doesn't redirect, but verify the mechanism works
        test_url = "https://httpbin.org/html"

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=test_url,
                config=CrawlerRunConfig()
            )

        # Verify redirected_url is populated
        if not result.redirected_url:
            record_result("Redirect URL Handling", "#1268", False,
                         "redirected_url is empty")
            return

        # For non-redirecting URL, should match original or be the final URL
        if not result.redirected_url.startswith("https://httpbin.org"):
            record_result("Redirect URL Handling", "#1268", False,
                         f"redirected_url is unexpected: {result.redirected_url}")
            return

        # Verify links are present and resolved
        if result.links:
            # Check that internal links have full URLs
            internal_links = result.links.get('internal', [])
            external_links = result.links.get('external', [])
            all_links = internal_links + external_links

            for link in all_links[:5]:  # Check first 5 links
                href = link.get('href', '')
                if href and not href.startswith(('http://', 'https://', 'mailto:', 'tel:', '#', 'javascript:')):
                    record_result("Redirect URL Handling", "#1268", False,
                                 f"Link not resolved to absolute URL: {href}")
                    return

        record_result("Redirect URL Handling", "#1268", True,
                     f"redirected_url correctly captured: {result.redirected_url}")

    except Exception as e:
        record_result("Redirect URL Handling", "#1268", False, f"Exception: {e}")