async def test_bm25_dedup():
    """
    Crawl a page using BM25ContentFilter and verify no duplicate chunks
    in fit_markdown.

    NEW in v0.8.5: BM25ContentFilter.filter_content() deduplicates output
    chunks, keeping the first occurrence in document order.
    """
    print_test("BM25 Deduplication", "fit_markdown has no duplicates")

    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
        from crawl4ai.content_filter_strategy import BM25ContentFilter
        from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                "https://quotes.toscrape.com",
                config=CrawlerRunConfig(
                    markdown_generator=DefaultMarkdownGenerator(
                        content_filter=BM25ContentFilter(
                            user_query="famous quotes about life",
                        ),
                    ),
                ),
            )

        if not result.success:
            record_result("BM25 Dedup", "fit_markdown", False,
                         f"Crawl failed: {result.error_message}")
            return

        fit_md = result.markdown.fit_markdown if result.markdown else ""
        if not fit_md:
            record_result("BM25 Dedup", "fit_markdown", False,
                         "No fit_markdown produced")
            return

        # Check for duplicate lines (non-empty, non-header)
        lines = [l.strip() for l in fit_md.split("\n") if l.strip() and not l.startswith("#")]
        unique_lines = list(dict.fromkeys(lines))  # preserves order
        dupes = len(lines) - len(unique_lines)

        if dupes > 0:
            record_result("BM25 Dedup", "fit_markdown", False,
                         f"{dupes} duplicate lines found in fit_markdown")
            return

        record_result("BM25 Dedup", "fit_markdown dedup", True,
                     f"No duplicates in fit_markdown ({len(unique_lines)} unique lines)")

    except Exception as e:
        record_result("BM25 Dedup", "fit_markdown", False, f"Exception: {e}")