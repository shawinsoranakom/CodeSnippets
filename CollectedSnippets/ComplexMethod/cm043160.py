async def adaptive_crawling_demo(auto_mode=False):
    """
    🎯 Adaptive Crawling Demo
    Shows intelligent crawling that knows when to stop
    """
    print_banner(
        "🎯 ADAPTIVE CRAWLING",
        "Intelligent crawling that knows when it has enough information"
    )

    # Explain the feature
    console.print(Panel(
        "[bold]What is Adaptive Crawling?[/bold]\n\n"
        "Adaptive Crawling intelligently determines when sufficient information has been gathered:\n\n"
        "• [cyan]Confidence Tracking[/cyan]: Monitors how well we understand the topic (0-100%)\n"
        "• [magenta]Smart Exploration[/magenta]: Follows most promising links based on relevance\n"
        "• [green]Early Stopping[/green]: Stops when confidence threshold is reached\n"
        "• [yellow]Two Strategies[/yellow]: Statistical (fast) vs Embedding (semantic)\n\n"
        "Perfect for research tasks where you need 'just enough' information!",
        title="Feature Overview",
        border_style="blue"
    ))

    await asyncio.sleep(2)

    # Demo 1: Basic adaptive crawling with confidence visualization
    console.print("\n[bold yellow]Demo 1: Statistical Strategy - Fast Topic Understanding[/bold yellow]\n")

    query = "Python async web scraping best practices"
    console.print(f"[cyan]🔍 Research Query:[/cyan] [bold]{query}[/bold]")
    console.print(f"[cyan]🎯 Goal:[/cyan] Gather enough information to understand the topic")
    console.print(f"[cyan]📊 Strategy:[/cyan] Statistical (keyword-based, fast)\n")

    # Configure adaptive crawler
    config = AdaptiveConfig(
        strategy="statistical",
        max_pages=3,  # Limit to 3 pages for demo
        confidence_threshold=0.7,  # Stop at 70% confidence
        top_k_links=2,  # Follow top 2 links per page
        min_gain_threshold=0.05  # Need 5% information gain to continue
    )

    async with AsyncWebCrawler(verbose=False) as crawler:
        adaptive = AdaptiveCrawler(crawler, config)

        # Create progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            # Track crawling progress
            crawl_task = progress.add_task("[cyan]Starting adaptive crawl...", total=None)

            # Start crawling
            start_time = time.time()
            result = await adaptive.digest(
                start_url="https://docs.python.org/3/library/asyncio.html",
                query=query
            )
            elapsed = time.time() - start_time

            progress.remove_task(crawl_task)

        # Display results with visual confidence meter
        console.print(f"\n[bold green]✅ Crawling Complete in {elapsed:.1f} seconds![/bold green]\n")

        # Create confidence visualization
        confidence = adaptive.confidence
        conf_percentage = int(confidence * 100)
        conf_bar = "█" * (conf_percentage // 5) + "░" * (20 - conf_percentage // 5)

        console.print(f"[bold]Confidence Level:[/bold] [{('green' if confidence >= 0.7 else 'yellow' if confidence >= 0.5 else 'red')}]{conf_bar}[/] {conf_percentage}%")

        # Show crawl statistics
        stats_table = Table(
            title="📊 Crawl Statistics",
            box=box.ROUNDED,
            show_lines=True
        )

        stats_table.add_column("Metric", style="cyan", width=25)
        stats_table.add_column("Value", style="white", width=20)

        stats_table.add_row("Pages Crawled", str(len(result.crawled_urls)))
        stats_table.add_row("Knowledge Base Size", f"{len(adaptive.state.knowledge_base)} documents")
        # Calculate total content from CrawlResult objects
        total_content = 0
        for doc in adaptive.state.knowledge_base:
            if hasattr(doc, 'markdown') and doc.markdown and hasattr(doc.markdown, 'raw_markdown'):
                total_content += len(doc.markdown.raw_markdown)
        stats_table.add_row("Total Content", f"{total_content:,} chars")
        stats_table.add_row("Time per Page", f"{elapsed / len(result.crawled_urls):.2f}s")

        console.print(stats_table)

        # Show top relevant pages
        console.print("\n[bold]🏆 Most Relevant Pages Found:[/bold]")
        relevant_pages = adaptive.get_relevant_content(top_k=3)
        for i, page in enumerate(relevant_pages, 1):
            console.print(f"\n{i}. [bold]{page['url']}[/bold]")
            console.print(f"   Relevance: {page['score']:.2%}")

            # Show key information extracted
            content = page['content'] or ""
            if content:
                # Find most relevant sentence
                sentences = [s.strip() for s in content.split('.') if s.strip()]
                if sentences:
                    console.print(f"   [dim]Key insight: {sentences[0]}...[/dim]")

    if not auto_mode:
        console.print("\n[dim]Press Enter to continue to Demo 2...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Demo 2: Early Stopping Demonstration
    console.print("\n[bold yellow]Demo 2: Early Stopping - Stop When We Know Enough[/bold yellow]\n")

    query2 = "Python requests library tutorial"
    console.print(f"[cyan]🔍 Research Query:[/cyan] [bold]{query2}[/bold]")
    console.print(f"[cyan]🎯 Goal:[/cyan] Stop as soon as we reach 60% confidence")
    console.print("[dim]Watch how adaptive crawling stops early when it has enough info[/dim]\n")

    # Configure for early stopping
    early_stop_config = AdaptiveConfig(
        strategy="statistical",
        max_pages=10,  # Allow up to 10, but will stop early
        confidence_threshold=0.6,  # Lower threshold for demo
        top_k_links=2
    )

    async with AsyncWebCrawler(verbose=False) as crawler:
        adaptive_early = AdaptiveCrawler(crawler, early_stop_config)

        # Track progress
        console.print("[cyan]Starting crawl with early stopping enabled...[/cyan]")
        start_time = time.time()

        result = await adaptive_early.digest(
            start_url="https://docs.python-requests.org/en/latest/",
            query=query2
        )

        elapsed = time.time() - start_time

        # Show results
        console.print(f"\n[bold green]✅ Stopped early at {int(adaptive_early.confidence * 100)}% confidence![/bold green]")
        console.print(f"• Crawled only {len(result.crawled_urls)} pages (max was 10)")
        console.print(f"• Saved time: ~{elapsed:.1f}s total")
        console.print(f"• Efficiency: {elapsed / len(result.crawled_urls):.1f}s per page\n")

        # Show why it stopped
        if adaptive_early.confidence >= 0.6:
            console.print("[green]✓ Reached confidence threshold - no need to crawl more![/green]")
        else:
            console.print("[yellow]⚠ Hit max pages limit before reaching threshold[/yellow]")

    if not auto_mode:
        console.print("\n[dim]Press Enter to continue to Demo 3...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Demo 3: Knowledge Base Export/Import
    console.print("\n[bold yellow]Demo 3: Knowledge Base Export & Import[/bold yellow]\n")

    query3 = "Python decorators tutorial"
    console.print(f"[cyan]🔍 Research Query:[/cyan] [bold]{query3}[/bold]")
    console.print("[dim]Build knowledge base, export it, then import for continued research[/dim]\n")

    # First crawl - build knowledge base
    export_config = AdaptiveConfig(
        strategy="statistical",
        max_pages=2,  # Small for demo
        confidence_threshold=0.5
    )

    async with AsyncWebCrawler(verbose=False) as crawler:
        # Phase 1: Initial research
        console.print("[bold]Phase 1: Initial Research[/bold]")
        adaptive1 = AdaptiveCrawler(crawler, export_config)

        result1 = await adaptive1.digest(
            start_url="https://realpython.com/",
            query=query3
        )

        console.print(f"✓ Built knowledge base with {len(adaptive1.state.knowledge_base)} documents")
        console.print(f"✓ Confidence: {int(adaptive1.confidence * 100)}%\n")

        # Export knowledge base
        console.print("[bold]💾 Exporting Knowledge Base:[/bold]")
        kb_export = adaptive1.export_knowledge_base()

        export_stats = {
            "documents": len(kb_export['documents']),
            "urls": len(kb_export['visited_urls']),
            "size": len(json.dumps(kb_export)),
            "confidence": kb_export['confidence']
        }

        for key, value in export_stats.items():
            console.print(f"• {key.capitalize()}: {value:,}" if isinstance(value, int) else f"• {key.capitalize()}: {value:.2%}")

        # Phase 2: Import and continue
        console.print("\n[bold]Phase 2: Import & Continue Research[/bold]")
        adaptive2 = AdaptiveCrawler(crawler, export_config)

        # Import the knowledge base
        await adaptive2.import_knowledge_base(kb_export)
        console.print(f"✓ Imported {len(adaptive2.state.knowledge_base)} documents")
        console.print(f"✓ Starting confidence: {int(adaptive2.confidence * 100)}%")

        # Continue research from a different starting point
        console.print("\n[cyan]Continuing research from a different angle...[/cyan]")
        result2 = await adaptive2.digest(
            start_url="https://docs.python.org/3/glossary.html#term-decorator",
            query=query3
        )

        console.print(f"\n[bold green]✅ Research Complete![/bold green]")
        console.print(f"• Total documents: {len(adaptive2.state.knowledge_base)}")
        console.print(f"• Final confidence: {int(adaptive2.confidence * 100)}%")
        console.print(f"• Knowledge preserved across sessions!")

    # Summary
    console.print("\n[bold green]✨ Adaptive Crawling Benefits:[/bold green]")
    console.print("• Automatically stops when enough information is gathered")
    console.print("• Follows most promising links based on relevance")
    console.print("• Saves time and resources with intelligent exploration")
    console.print("• Export/import knowledge bases for continued research")
    console.print("• Choose strategy based on needs: speed vs semantic understanding\n")