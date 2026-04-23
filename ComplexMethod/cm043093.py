async def example_two_phase_crawl():
    """
    Example 3: Two-phase crawling pattern.

    Phase 1: Fast discovery with prefetch
    Phase 2: Full processing on selected URLs
    """
    print("\n" + "=" * 60)
    print("Example 3: Two-Phase Crawling")
    print("=" * 60)

    async with AsyncWebCrawler(verbose=False) as crawler:
        # ═══════════════════════════════════════════════════════════
        # Phase 1: Fast URL discovery
        # ═══════════════════════════════════════════════════════════
        print("\n--- Phase 1: Fast Discovery ---")

        prefetch_config = CrawlerRunConfig(prefetch=True)
        start = time.time()
        discovery = await crawler.arun("https://books.toscrape.com", config=prefetch_config)
        discovery_time = time.time() - start

        all_urls = [link["href"] for link in discovery.links.get("internal", [])]
        print(f"  Discovered {len(all_urls)} URLs in {discovery_time:.2f}s")

        # Filter to URLs we care about (e.g., book detail pages)
        # On books.toscrape.com, book pages contain "catalogue/" but not "category/"
        book_urls = [
            url for url in all_urls
            if "catalogue/" in url and "category/" not in url
        ][:5]  # Limit to 5 for demo

        print(f"  Filtered to {len(book_urls)} book pages")

        # ═══════════════════════════════════════════════════════════
        # Phase 2: Full processing on selected URLs
        # ═══════════════════════════════════════════════════════════
        print("\n--- Phase 2: Full Processing ---")

        full_config = CrawlerRunConfig(
            word_count_threshold=10,
            remove_overlay_elements=True,
        )

        results = []
        start = time.time()

        for url in book_urls:
            result = await crawler.arun(url, config=full_config)
            if result.success:
                results.append(result)
                title = result.url.split("/")[-2].replace("-", " ").title()[:40]
                md_len = len(result.markdown.raw_markdown) if result.markdown else 0
                print(f"    Processed: {title}... ({md_len} chars)")

        processing_time = time.time() - start
        print(f"\n  Processed {len(results)} pages in {processing_time:.2f}s")

        # ═══════════════════════════════════════════════════════════
        # Summary
        # ═══════════════════════════════════════════════════════════
        print(f"\n--- Summary ---")
        print(f"  Discovery phase: {discovery_time:.2f}s ({len(all_urls)} URLs)")
        print(f"  Processing phase: {processing_time:.2f}s ({len(results)} pages)")
        print(f"  Total time: {discovery_time + processing_time:.2f}s")
        print(f"  URLs skipped: {len(all_urls) - len(book_urls)} (not matching filter)")