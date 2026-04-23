async def url_seeder_demo(auto_mode=False):
    """
    🌱 URL Seeder Demo
    Shows intelligent URL discovery and filtering
    """
    print_banner(
        "🌱 URL SEEDER - INTELLIGENT URL DISCOVERY",
        "Pre-discover and filter URLs before crawling"
    )

    # Explain the feature
    console.print(Panel(
        "[bold]What is URL Seeder?[/bold]\n\n"
        "URL Seeder enables intelligent crawling at scale by pre-discovering URLs:\n\n"
        "• [cyan]Discovery[/cyan]: Find all URLs from sitemaps or by crawling\n"
        "• [magenta]Filtering[/magenta]: Filter by patterns, dates, or content\n"
        "• [green]Ranking[/green]: Score URLs by relevance (BM25 or semantic)\n"
        "• [yellow]Metadata[/yellow]: Extract head data without full crawl\n\n"
        "Perfect for targeted crawling of large websites!",
        title="Feature Overview",
        border_style="blue"
    ))

    await asyncio.sleep(2)

    # Demo 1: Basic URL discovery
    console.print("\n[bold yellow]Demo 1: Discover URLs from Sitemap[/bold yellow]\n")

    target_site = "realpython.com"
    console.print(f"[cyan]🔍 Target:[/cyan] [bold]{target_site}[/bold]")
    console.print("[dim]Let's discover what content is available[/dim]\n")

    async with AsyncUrlSeeder() as seeder:
        # First, see total URLs available
        console.print("[cyan]Discovering ALL URLs from sitemap...[/cyan]")

        all_urls = await seeder.urls(
            target_site, 
            SeedingConfig(source="sitemap")
        )

        console.print(f"[green]✅ Found {len(all_urls)} total URLs![/green]\n")

        # Show URL categories
        categories = {}
        for url_info in all_urls[:100]:  # Sample first 100
            url = url_info['url']
            if '/tutorials/' in url:
                categories['tutorials'] = categories.get('tutorials', 0) + 1
            elif '/python-' in url:
                categories['python-topics'] = categories.get('python-topics', 0) + 1
            elif '/courses/' in url:
                categories['courses'] = categories.get('courses', 0) + 1
            else:
                categories['other'] = categories.get('other', 0) + 1

        console.print("[bold]URL Categories (sample of first 100):[/bold]")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            console.print(f"• {cat}: {count} URLs")

    if not auto_mode:
        console.print("\n[dim]Press Enter to continue to Demo 2...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Demo 2: Pattern filtering
    console.print("\n[bold yellow]Demo 2: Filter URLs by Pattern[/bold yellow]\n")

    pattern = "*python-basics*"
    console.print(f"[cyan]🎯 Pattern:[/cyan] [bold]{pattern}[/bold]")
    console.print("[dim]Finding Python basics tutorials[/dim]\n")

    async with AsyncUrlSeeder() as seeder:
        filtered_urls = await seeder.urls(
            target_site,
            SeedingConfig(
                source="sitemap",
                pattern=pattern,
                max_urls=10
            )
        )

        console.print(f"[green]✅ Found {len(filtered_urls)} Python basics URLs:[/green]\n")

        for i, url_info in enumerate(filtered_urls[:5], 1):
            console.print(f"{i}. {url_info['url']}")

    if not auto_mode:
        console.print("\n[dim]Press Enter to continue to Demo 3...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Demo 3: Smart search with BM25 ranking
    console.print("\n[bold yellow]Demo 3: Smart Search with BM25 Ranking[/bold yellow]\n")

    query = "web scraping beautifulsoup tutorial"
    console.print(f"[cyan]🔍 Query:[/cyan] [bold]{query}[/bold]")
    console.print("[dim]Using BM25 to find most relevant content[/dim]\n")

    async with AsyncUrlSeeder() as seeder:
        # Search with relevance scoring
        results = await seeder.urls(
            target_site,
            SeedingConfig(
                source="sitemap",
                pattern="*beautiful-soup*",  # Find Beautiful Soup pages
                extract_head=True,  # Get metadata
                query=query,
                scoring_method="bm25",
                # No threshold - show all results ranked by BM25
                max_urls=10
            )
        )

        console.print(f"[green]✅ Top {len(results)} most relevant results:[/green]\n")

        # Create a table for results
        table = Table(
            title="🎯 Relevance-Ranked Results",
            box=box.ROUNDED,
            show_lines=True
        )

        table.add_column("Rank", style="cyan", width=6)
        table.add_column("Score", style="yellow", width=8)
        table.add_column("Title", style="white", width=50)
        table.add_column("URL", style="dim", width=40)

        for i, result in enumerate(results[:5], 1):
            score = result.get('relevance_score', 0)
            title = result.get('head_data', {}).get('title', 'No title')[:50]
            url = result['url'].split('/')[-2]  # Just the slug

            table.add_row(
                f"#{i}",
                f"{score:.3f}",
                title,
                f".../{url}/"
            )

        console.print(table)

    if not auto_mode:
        console.print("\n[dim]Press Enter to continue to Demo 4...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Demo 4: Complete pipeline - Discover → Filter → Crawl
    console.print("\n[bold yellow]Demo 4: Complete Pipeline - Discover → Filter → Crawl[/bold yellow]\n")

    console.print("[cyan]Let's build a complete crawling pipeline:[/cyan]")
    console.print("1. Discover URLs about Python decorators")
    console.print("2. Filter and rank by relevance")
    console.print("3. Crawl top results\n")

    async with AsyncUrlSeeder() as seeder:
        # Step 1: Discover and filter
        console.print("[bold]Step 1: Discovering decorator tutorials...[/bold]")

        decorator_urls = await seeder.urls(
            target_site,
            SeedingConfig(
                source="sitemap",
                pattern="*decorator*",
                extract_head=True,
                query="python decorators tutorial examples",
                scoring_method="bm25",
                max_urls=5
            )
        )

        console.print(f"Found {len(decorator_urls)} relevant URLs\n")

        # Step 2: Show what we'll crawl
        console.print("[bold]Step 2: URLs to crawl (ranked by relevance):[/bold]")
        urls_to_crawl = []
        for i, url_info in enumerate(decorator_urls[:3], 1):
            urls_to_crawl.append(url_info['url'])
            title = url_info.get('head_data', {}).get('title', 'No title')
            console.print(f"{i}. {title[:60]}...")
            console.print(f"   [dim]{url_info['url']}[/dim]")

        # Step 3: Crawl them
        console.print("\n[bold]Step 3: Crawling selected URLs...[/bold]")

        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(
                only_text=True,
                cache_mode=CacheMode.BYPASS
            )

            # Crawl just the first URL for demo
            if urls_to_crawl:
                console.print(f"\n[dim]Crawling first URL: {urls_to_crawl[0]}[/dim]")
                result = await crawler.arun(urls_to_crawl[0], config=config)

                if result.success:
                    console.print(f"\n[green]✅ Successfully crawled the page![/green]")
                    console.print("\n[bold]Sample content:[/bold]")
                    content = result.markdown.raw_markdown[:300].replace('\n', ' ')
                    console.print(f"[dim]{content}...[/dim]")
                else:
                    console.print(f"[red]Failed to crawl: {result.error_message}[/red]")

    # Show code example
    console.print("\n[bold yellow]Code Example:[/bold yellow]\n")

    code = '''# Complete URL Seeder pipeline
async with AsyncUrlSeeder() as seeder:
    # 1. Discover and filter URLs
    urls = await seeder.urls(
        "example.com",
        SeedingConfig(
            source="sitemap",              # or "crawl" 
            pattern="*tutorial*",          # URL pattern
            extract_head=True,             # Get metadata
            query="python web scraping",   # Search query
            scoring_method="bm25",         # Ranking method
            score_threshold=0.2,           # Quality filter
            max_urls=10                    # Max URLs
        )
    )

    # 2. Extract just the URLs
    urls_to_crawl = [u["url"] for u in urls[:5]]

    # 3. Crawl them efficiently
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(urls_to_crawl)

        async for result in results:
            if result.success:
                print(f"Crawled: {result.url}")
                # Process content...'''

    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="Implementation", border_style="green"))

    # Summary
    console.print("\n[bold green]✨ URL Seeder Benefits:[/bold green]")
    console.print("• Pre-discover URLs before crawling - save time!")
    console.print("• Filter by patterns, dates, or content relevance")
    console.print("• Rank URLs by BM25 or semantic similarity")
    console.print("• Extract metadata without full crawl")
    console.print("• Perfect for large-scale targeted crawling\n")