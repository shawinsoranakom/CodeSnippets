async def test_gfm_tables():
    """
    Crawl a page containing HTML tables and verify the markdown output
    has proper GFM pipe delimiters.

    NEW in v0.8.5: html2text now generates | col1 | col2 | with proper
    leading/trailing pipes instead of col1 | col2.
    """
    print_test("GFM Table Compliance", "crawl page with tables")

    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

        # Use raw HTML with a table
        html = """
        <html><body>
            <h1>Product Comparison</h1>
            <table>
                <tr><th>Product</th><th>Price</th><th>Rating</th></tr>
                <tr><td>Widget A</td><td>$9.99</td><td>4.5</td></tr>
                <tr><td>Widget B</td><td>$14.99</td><td>4.8</td></tr>
            </table>
        </body></html>
        """

        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                f"raw:{html}",
                config=CrawlerRunConfig(),
            )

        if not result.success or not result.markdown:
            record_result("GFM Tables", "table crawl", False,
                         "Crawl failed or no markdown")
            return

        md = result.markdown.raw_markdown
        table_lines = [
            l.strip() for l in md.split("\n")
            if l.strip() and "|" in l
        ]

        if not table_lines:
            record_result("GFM Tables", "pipe delimiters", False,
                         f"No table lines found in markdown:\n{md}")
            return

        all_have_pipes = all(
            l.startswith("|") and l.endswith("|")
            for l in table_lines
        )

        if not all_have_pipes:
            record_result("GFM Tables", "pipe delimiters", False,
                         f"Missing leading/trailing pipes:\n" +
                         "\n".join(table_lines))
            return

        record_result("GFM Tables", "pipe delimiters via crawl", True,
                     f"Table has proper GFM pipes ({len(table_lines)} rows)")

    except Exception as e:
        record_result("GFM Tables", "pipe delimiters", False, f"Exception: {e}")