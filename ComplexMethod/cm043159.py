async def link_preview_demo(auto_mode=False):
    """
    🔗 Link Preview/Peek Demo
    Showcases the 3-layer scoring system for intelligent link analysis
    """
    print_banner(
        "🔗 LINK PREVIEW & INTELLIGENT SCORING",
        "Advanced link analysis with intrinsic, contextual, and total scoring"
    )

    # Explain the feature
    console.print(Panel(
        "[bold]What is Link Preview?[/bold]\n\n"
        "Link Preview analyzes links on a page with a sophisticated 3-layer scoring system:\n\n"
        "• [cyan]Intrinsic Score[/cyan]: Quality based on link text, position, and attributes (0-10)\n"
        "• [magenta]Contextual Score[/magenta]: Relevance to your query using semantic analysis (0-1)\n"
        "• [green]Total Score[/green]: Combined score for intelligent prioritization\n\n"
        "This helps you find the most relevant and high-quality links automatically!",
        title="Feature Overview",
        border_style="blue"
    ))

    await asyncio.sleep(2)

    # Demo 1: Basic link analysis with visual scoring
    console.print("\n[bold yellow]Demo 1: Analyzing Python Documentation Links[/bold yellow]\n")

    query = "async await coroutines tutorial"
    console.print(f"[cyan]🔍 Query:[/cyan] [bold]{query}[/bold]")
    console.print("[dim]Looking for links related to asynchronous programming...[/dim]\n")

    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            include_external=False,
            max_links=10,
            concurrency=5,
            query=query,  # Our search context
            verbose=False  # We'll handle the display
        ),
        score_links=True,
        only_text=True
    )

    # Create a progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Crawling and analyzing links...", total=None)

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://docs.python.org/3/library/asyncio.html", config=config)

        progress.remove_task(task)

    if result.success:
        # Extract links with scores
        links = result.links.get("internal", [])
        scored_links = [l for l in links if l.get("head_data") and l.get("total_score")]

        # Sort by total score
        scored_links.sort(key=lambda x: x.get("total_score", 0), reverse=True)

        # Create a beautiful table for results
        table = Table(
            title="🎯 Top Scored Links",
            box=box.ROUNDED,
            show_lines=True,
            title_style="bold magenta"
        )

        table.add_column("Rank", style="cyan", width=6)
        table.add_column("Link Text", style="white", width=40)
        table.add_column("Intrinsic Score", width=25)
        table.add_column("Contextual Score", width=25)
        table.add_column("Total Score", style="bold", width=15)

        for i, link in enumerate(scored_links[:5], 1):
            intrinsic = link.get('intrinsic_score', 0)
            contextual = link.get('contextual_score', 0)
            total = link.get('total_score', 0)

            # Get link text and title
            text = link.get('text', '')[:35] + "..." if len(link.get('text', '')) > 35 else link.get('text', '')
            title = link.get('head_data', {}).get('title', 'No title')[:40]

            table.add_row(
                f"#{i}",
                text or title,
                create_score_bar(intrinsic, 10.0),
                create_score_bar(contextual, 1.0),
                f"[bold green]{total:.3f}[/bold green]"
            )

        console.print(table)

        # Show what makes a high-scoring link
        if scored_links:
            best_link = scored_links[0]
            console.print(f"\n[bold green]🏆 Best Match:[/bold green]")
            console.print(f"URL: [link]{best_link['href']}[/link]")
            console.print(f"Title: {best_link.get('head_data', {}).get('title', 'N/A')}")

            desc = best_link.get('head_data', {}).get('meta', {}).get('description', '')
            if desc:
                console.print(f"Description: [dim]{desc[:100]}...[/dim]")

    if not auto_mode:
        console.print("\n[dim]Press Enter to continue to Demo 2...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Demo 2: Research Assistant Mode
    console.print("\n[bold yellow]Demo 2: Research Assistant - Finding Machine Learning Resources[/bold yellow]\n")

    # First query - will find no results
    query1 = "deep learning neural networks beginners tutorial"
    console.print(f"[cyan]🔍 Query 1:[/cyan] [bold]{query1}[/bold]")
    console.print("[dim]Note: scikit-learn focuses on traditional ML, not deep learning[/dim]\n")

    # Configure for research mode
    research_config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            include_external=True,
            query=query1,
            max_links=20,
            score_threshold=0.3,  # Only high-relevance links
            concurrency=10
        ),
        score_links=True
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Discovering learning resources...", total=None)

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://scikit-learn.org/stable/", config=research_config)

        progress.remove_task(task)

    if result.success:
        all_links = result.links.get("internal", []) + result.links.get("external", [])
        # Filter for links with actual scores
        relevant_links = [l for l in all_links if l.get("total_score") is not None and l.get("total_score") > 0.3]
        relevant_links.sort(key=lambda x: x.get("total_score", 0), reverse=True)

        console.print(f"[bold green]📚 Found {len(relevant_links)} highly relevant resources![/bold green]\n")

        # Group by score ranges
        excellent = [l for l in relevant_links if l.get("total_score", 0) > 0.7]
        good = [l for l in relevant_links if 0.5 <= l.get("total_score", 0) <= 0.7]
        fair = [l for l in relevant_links if 0.3 <= l.get("total_score", 0) < 0.5]

        if excellent:
            console.print("[bold green]⭐⭐⭐ Excellent Matches:[/bold green]")
            for link in excellent[:3]:
                title = link.get('head_data', {}).get('title', link.get('text', 'No title'))
                console.print(f"  • {title[:60]}... [dim]({link.get('total_score', 0):.2f})[/dim]")

        if good:
            console.print("\n[yellow]⭐⭐ Good Matches:[/yellow]")
            for link in good[:3]:
                title = link.get('head_data', {}).get('title', link.get('text', 'No title'))
                console.print(f"  • {title[:60]}... [dim]({link.get('total_score', 0):.2f})[/dim]")

    # Second query - will find results
    console.print("\n[bold cyan]Let's try a more relevant query for scikit-learn:[/bold cyan]\n")

    query2 = "machine learning classification tutorial examples"
    console.print(f"[cyan]🔍 Query 2:[/cyan] [bold]{query2}[/bold]")
    console.print("[dim]This should find relevant content about traditional ML[/dim]\n")

    research_config2 = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            include_external=True,
            query=query2,
            max_links=15,
            score_threshold=0.2,  # Slightly lower threshold
            concurrency=10
        ),
        score_links=True
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Finding ML tutorials...", total=None)

        async with AsyncWebCrawler() as crawler:
            result2 = await crawler.arun("https://scikit-learn.org/stable/", config=research_config2)

        progress.remove_task(task)

    if result2.success:
        all_links2 = result2.links.get("internal", []) + result2.links.get("external", [])
        relevant_links2 = [l for l in all_links2 if l.get("total_score") is not None and l.get("total_score") > 0.2]
        relevant_links2.sort(key=lambda x: x.get("total_score", 0), reverse=True)

        console.print(f"[bold green]📚 Now found {len(relevant_links2)} relevant resources![/bold green]\n")

        if relevant_links2:
            console.print("[bold]Top relevant links for ML tutorials:[/bold]")
            for i, link in enumerate(relevant_links2[:5], 1):
                title = link.get('head_data', {}).get('title', link.get('text', 'No title'))
                score = link.get('total_score', 0)
                console.print(f"{i}. [{score:.3f}] {title[:70]}...")

    if not auto_mode:
        console.print("\n[dim]Press Enter to continue to Demo 3...[/dim]")
        input()
    else:
        await asyncio.sleep(1)

    # Demo 3: Live scoring visualization
    console.print("\n[bold yellow]Demo 3: Understanding the 3-Layer Scoring System[/bold yellow]\n")

    demo_query = "async programming tutorial"
    console.print(f"[cyan]🔍 Query:[/cyan] [bold]{demo_query}[/bold]")
    console.print("[dim]Let's see how different link types score against this query[/dim]\n")

    # Create a sample link analysis
    sample_links = [
        {
            "text": "Complete Guide to Async Programming",
            "intrinsic": 9.2,
            "contextual": 0.95,
            "factors": ["Strong keywords", "Title position", "Descriptive text"]
        },
        {
            "text": "API Reference",
            "intrinsic": 6.5,
            "contextual": 0.15,
            "factors": ["Common link text", "Navigation menu", "Low relevance"]
        },
        {
            "text": "Click here",
            "intrinsic": 2.1,
            "contextual": 0.05,
            "factors": ["Poor link text", "No context", "Generic anchor"]
        }
    ]

    for link in sample_links:
        total = (link["intrinsic"] / 10 * 0.4) + (link["contextual"] * 0.6)

        panel_content = (
            f"[bold]Link Text:[/bold] {link['text']}\n\n"
            f"[cyan]Intrinsic Score:[/cyan] {create_score_bar(link['intrinsic'], 10.0)}\n"
            f"[magenta]Contextual Score:[/magenta] {create_score_bar(link['contextual'], 1.0)}\n"
            f"[green]Total Score:[/green] {total:.3f}\n\n"
            f"[dim]Factors: {', '.join(link['factors'])}[/dim]"
        )

        console.print(Panel(
            panel_content,
            title=f"Link Analysis",
            border_style="blue" if total > 0.7 else "yellow" if total > 0.3 else "red"
        ))
        await asyncio.sleep(1)

    # Summary
    console.print("\n[bold green]✨ Link Preview Benefits:[/bold green]")
    console.print("• Automatically finds the most relevant links for your research")
    console.print("• Saves time by prioritizing high-quality content")
    console.print("• Provides semantic understanding beyond simple keyword matching")
    console.print("• Enables intelligent crawling decisions\n")