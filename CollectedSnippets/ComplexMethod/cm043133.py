async def crawl_selected_urls(urls: List[str], query: str, config: ResearchConfig) -> List[Dict]:
    """
    Crawl selected URLs with content filtering:
    - Use AsyncWebCrawler.arun_many()
    - Apply content filter
    - Generate clean markdown
    """
    # Extract just URLs from the discovery results
    url_list = [u['url'] for u in urls if 'url' in u][:config.max_urls_to_crawl]

    if not url_list:
        console.print("[red]❌ No URLs to crawl[/red]")
        return []

    console.print(f"\n[cyan]🕷️ Crawling {len(url_list)} URLs...[/cyan]")

    # Check cache for each URL
    crawled_results = []
    urls_to_crawl = []

    for url in url_list:
        cache_key = get_cache_key("crawled_content", url, query)
        cached_content = load_from_cache(cache_key)
        if cached_content and not config.force_refresh:
            crawled_results.append(cached_content)
        else:
            urls_to_crawl.append(url)

    if urls_to_crawl:
        console.print(f"[cyan]📥 Crawling {len(urls_to_crawl)} new URLs (cached: {len(crawled_results)})[/cyan]")

        # Configure markdown generator with content filter
        md_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,
                threshold_type="dynamic",
                min_word_threshold=10
            ),
        )

        # Configure crawler
        crawler_config = CrawlerRunConfig(
            markdown_generator=md_generator,
            exclude_external_links=True,
            excluded_tags=['nav', 'header', 'footer', 'aside'],
        )

        # Create crawler with browser config
        async with AsyncWebCrawler(
            config=BrowserConfig(
                headless=config.headless,
                verbose=config.verbose
            )
        ) as crawler:
            # Crawl URLs
            results = await crawler.arun_many(
                urls_to_crawl,
                config=crawler_config,
                max_concurrent=config.max_concurrent_crawls
            )

            # Process results
            for url, result in zip(urls_to_crawl, results):
                if result.success:
                    content_data = {
                        'url': url,
                        'title': result.metadata.get('title', ''),
                        'markdown': result.markdown.fit_markdown or result.markdown.raw_markdown,
                        'raw_length': len(result.markdown.raw_markdown),
                        'fit_length': len(result.markdown.fit_markdown) if result.markdown.fit_markdown else len(result.markdown.raw_markdown),
                        'metadata': result.metadata
                    }
                    crawled_results.append(content_data)

                    # Cache the result
                    cache_key = get_cache_key("crawled_content", url, query)
                    save_to_cache(cache_key, content_data)
                else:
                    console.print(f"  [red]❌ Failed: {url[:50]}... - {result.error}[/red]")

    console.print(f"[green]✅ Successfully crawled {len(crawled_results)} URLs[/green]")
    return crawled_results