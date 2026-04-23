async def test_prefetch_two_phase():
    """
    Verify the two-phase crawl pattern: prefetch for discovery, then full processing.

    NEW in v0.8.0: Prefetch mode enables efficient two-phase crawling where
    you discover URLs quickly, then selectively process important ones.
    """
    print_test("Prefetch Mode - Two-Phase Crawl", "Two-Phase Pattern")

    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

        async with AsyncWebCrawler(verbose=False) as crawler:
            # Phase 1: Fast discovery with prefetch
            prefetch_config = CrawlerRunConfig(prefetch=True)

            start = time.time()
            discovery = await crawler.arun("https://books.toscrape.com", config=prefetch_config)
            prefetch_time = time.time() - start

            all_urls = [link["href"] for link in discovery.links.get("internal", [])]

            # Filter to specific pages (e.g., book detail pages)
            book_urls = [
                url for url in all_urls
                if "catalogue/" in url and "category/" not in url
            ][:2]  # Just 2 for demo

            print(f"  Phase 1: Found {len(all_urls)} URLs in {prefetch_time:.2f}s")
            print(f"  Filtered to {len(book_urls)} book pages for full processing")

            if len(book_urls) == 0:
                record_result("Two-Phase Crawl", "Two-Phase Pattern", False,
                             "No book URLs found to process")
                return

            # Phase 2: Full processing on selected URLs
            full_config = CrawlerRunConfig()  # Normal mode

            start = time.time()
            processed = []
            for url in book_urls:
                result = await crawler.arun(url, config=full_config)
                if result.success and result.markdown:
                    processed.append(result)

            full_time = time.time() - start

            print(f"  Phase 2: Processed {len(processed)} pages in {full_time:.2f}s")

            if len(processed) == 0:
                record_result("Two-Phase Crawl", "Two-Phase Pattern", False,
                             "No pages successfully processed in phase 2")
                return

            # Verify full processing includes markdown
            if not processed[0].markdown or not processed[0].markdown.raw_markdown:
                record_result("Two-Phase Crawl", "Two-Phase Pattern", False,
                             "Full processing did not generate markdown")
                return

            record_result("Two-Phase Crawl", "Two-Phase Pattern", True,
                         f"Discovered {len(all_urls)} URLs (prefetch), processed {len(processed)} (full)")

    except Exception as e:
        record_result("Two-Phase Crawl", "Two-Phase Pattern", False, f"Exception: {e}")