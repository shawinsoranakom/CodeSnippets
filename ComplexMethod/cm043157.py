async def test_cleaned_html_attrs():
    """
    Crawl a page and verify cleaned_html retains class and id attributes.

    NEW in v0.8.5: 'class' and 'id' are now in IMPORTANT_ATTRS, so they
    survive HTML cleaning. Previously they were stripped.
    """
    print_test("cleaned_html Attributes", "class and id preserved")

    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

        html = """
        <html><body>
            <div id="main-content" class="container wide">
                <h1 class="page-title">Hello World</h1>
                <p id="intro" class="lead text-muted">Introduction paragraph.</p>
            </div>
        </body></html>
        """

        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                f"raw:{html}",
                config=CrawlerRunConfig(),
            )

        if not result.success or not result.cleaned_html:
            record_result("cleaned_html Attrs", "class/id", False,
                         "Crawl failed or no cleaned_html")
            return

        cleaned = result.cleaned_html
        checks = []

        if 'id="main-content"' in cleaned:
            checks.append("id=main-content")
        if 'class="container wide"' in cleaned or 'class="container' in cleaned:
            checks.append("class=container")
        if 'class="page-title"' in cleaned:
            checks.append("class=page-title")
        if 'id="intro"' in cleaned:
            checks.append("id=intro")

        if len(checks) < 2:
            record_result("cleaned_html Attrs", "class/id", False,
                         f"Only found {len(checks)} attrs: {checks}. "
                         f"cleaned_html snippet: {cleaned[:200]}")
            return

        record_result("cleaned_html Attrs", "class/id preserved", True,
                     f"Found {len(checks)} preserved attributes: {', '.join(checks)}")

    except Exception as e:
        record_result("cleaned_html Attrs", "class/id", False, f"Exception: {e}")