async def demo_part2_practical_crawling():
    """Part 2: Real-world example with different content types"""

    print_section("PART 2: Practical Multi-URL Crawling")
    print("Now let's see multi-config in action with real URLs.\n")

    # Create specialized configs for different content types
    configs = [
        # Config 1: PDF documents - only match files ending with .pdf
        CrawlerRunConfig(
            url_matcher="*.pdf",
            scraping_strategy=PDFContentScrapingStrategy()
        ),

        # Config 2: Blog/article pages with content filtering
        CrawlerRunConfig(
            url_matcher=["*/blog/*", "*/article/*", "*python.org*"],
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.48)
            )
        ),

        # Config 3: Dynamic pages requiring JavaScript
        CrawlerRunConfig(
            url_matcher=lambda url: 'github.com' in url,
            js_code="window.scrollTo(0, 500);"  # Scroll to load content
        ),

        # Config 4: Mixed matcher - API endpoints (string OR function)
        CrawlerRunConfig(
            url_matcher=[
                "*.json",  # String pattern for JSON files
                lambda url: 'api' in url or 'httpbin.org' in url  # Function for API endpoints
            ],
            match_mode=MatchMode.OR,
        ),

        # Config 5: Complex matcher - Secure documentation sites
        CrawlerRunConfig(
            url_matcher=[
                lambda url: url.startswith('https://'),  # Must be HTTPS
                "*.org/*",  # String: .org domain
                lambda url: any(doc in url for doc in ['docs', 'documentation', 'reference']),  # Has docs
                lambda url: not url.endswith(('.pdf', '.json'))  # Not PDF or JSON
            ],
            match_mode=MatchMode.AND,
            # wait_for="css:.content, css:article"  # Wait for content to load
        ),

        # Default config for everything else
        # CrawlerRunConfig()  # No url_matcher means it matches everything (use it as fallback)
    ]

    # URLs to crawl - each will use a different config
    urls = [
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",  # → PDF config
        "https://blog.python.org/",  # → Blog config with content filter
        "https://github.com/microsoft/playwright",  # → JS config
        "https://httpbin.org/json",  # → Mixed matcher config (API)
        "https://docs.python.org/3/reference/",  # → Complex matcher config
        "https://www.w3schools.com/",  # → Default config, if you uncomment the default config line above, if not you will see `Error: No matching configuration`
    ]

    print("URLs to crawl:")
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")

    print("\nCrawling with appropriate config for each URL...\n")

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=urls,
            config=configs
        )

        # Display results
        print("Results:")
        print("-" * 60)

        for result in results:
            if result.success:
                # Determine which config was used
                config_type = "Default"
                if result.url.endswith('.pdf'):
                    config_type = "PDF Strategy"
                elif any(pattern in result.url for pattern in ['blog', 'python.org']) and 'docs' not in result.url:
                    config_type = "Blog + Content Filter"
                elif 'github.com' in result.url:
                    config_type = "JavaScript Enabled"
                elif 'httpbin.org' in result.url or result.url.endswith('.json'):
                    config_type = "Mixed Matcher (API)"
                elif 'docs.python.org' in result.url:
                    config_type = "Complex Matcher (Secure Docs)"

                print(f"\n✓ {result.url}")
                print(f"  Config used: {config_type}")
                print(f"  Content size: {len(result.markdown)} chars")

                # Show if we have fit_markdown (from content filter)
                if hasattr(result.markdown, 'fit_markdown') and result.markdown.fit_markdown:
                    print(f"  Fit markdown size: {len(result.markdown.fit_markdown)} chars")
                    reduction = (1 - len(result.markdown.fit_markdown) / len(result.markdown)) * 100
                    print(f"  Content reduced by: {reduction:.1f}%")

                # Show extracted data if using extraction strategy
                if hasattr(result, 'extracted_content') and result.extracted_content:
                    print(f"  Extracted data: {str(result.extracted_content)[:100]}...")
            else:
                print(f"\n✗ {result.url}")
                print(f"  Error: {result.error_message}")

    print("\n" + "=" * 60)
    print("✅ Multi-config crawling complete!")
    print("\nBenefits demonstrated:")
    print("- PDFs handled with specialized scraper")
    print("- Blog content filtered for relevance") 
    print("- JavaScript executed only where needed")
    print("- Mixed matchers (string + function) for flexible matching")
    print("- Complex matchers for precise URL targeting")
    print("- Each URL got optimal configuration automatically!")