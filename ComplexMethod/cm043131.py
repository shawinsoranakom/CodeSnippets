async def section_5_keyword_filter_to_agent(seed: AsyncUrlSeeder):
    console.rule("[bold cyan]5. Complete Pipeline: Discover → Filter → Crawl")
    cfg = SeedingConfig(
        extract_head=True,
        concurrency=20,
        hits_per_sec=10,
        max_urls=10,
        pattern="*crawl4ai.com/*",
        force=True,
    )
    urls = await seed.urls(DOMAIN, cfg)

    keywords = ["deep crawling", "markdown", "llm"]
    selected = [u for u in urls if any(k in str(u["head_data"]).lower() for k in keywords)]

    console.print(f"[cyan]Selected {len(selected)} URLs with relevant keywords:")
    for u in selected[:10]:
        console.print("•", u["url"])

    console.print("\n[yellow]Passing above URLs to arun_many() LLM agent for crawling...")
    async with AsyncWebCrawler(verbose=True) as crawler:
        crawl_run_config = CrawlerRunConfig(
                # Example crawl settings for these URLs:
                only_text=True, # Just get text content
                screenshot=False,
                pdf=False,
                word_count_threshold=50, # Only process pages with at least 50 words
                stream=True,
                verbose=False # Keep logs clean for arun_many in this demo
            )

        # Extract just the URLs from the selected results
        urls_to_crawl = [u["url"] for u in selected]

        # We'll stream results for large lists, but collect them here for demonstration
        crawled_results_stream = await crawler.arun_many(urls_to_crawl, config=crawl_run_config)
        final_crawled_data = []
        async for result in crawled_results_stream:
            final_crawled_data.append(result)
            if len(final_crawled_data) % 5 == 0:
                print(f"   Processed {len(final_crawled_data)}/{len(urls_to_crawl)} URLs...")

        print(f"\n   Successfully crawled {len(final_crawled_data)} URLs.")
        if final_crawled_data:
            print("\n   Example of a crawled result's URL and Markdown (first successful one):")
            for result in final_crawled_data:
                if result.success and result.markdown.raw_markdown:
                    print(f"     URL: {result.url}")
                    print(f"     Markdown snippet: {result.markdown.raw_markdown[:200]}...")
                    break
            else:
                print("   No successful crawls with markdown found.")
        else:
            print("   No successful crawls found.")