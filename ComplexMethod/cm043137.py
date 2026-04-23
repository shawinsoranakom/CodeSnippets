async def main():
    """
    Main entry point for the BBC Sport Research Assistant
    """
    # Example queries
    example_queries = [
        "Premier League transfer news and rumors",
        "Champions League match results and analysis", 
        "World Cup qualifying updates",
        "Football injury reports and return dates",
        "Tennis grand slam tournament results"
    ]

    # Display header
    console.print(Panel.fit(
        "[bold cyan]BBC Sport Research Assistant[/bold cyan]\n\n"
        "This tool demonstrates efficient research using URLSeeder:\n"
        "[dim]• Discover all URLs without crawling\n"
        "• Filter and rank by relevance\n"
        "• Crawl only the most relevant content\n"
        "• Generate AI-powered insights with citations[/dim]\n\n"
        f"[dim]📁 Working directory: {SCRIPT_DIR}[/dim]",
        title="🔬 Welcome",
        border_style="cyan"
    ))

    # Configuration options table
    config_table = Table(title="\n⚙️  Configuration Options", show_header=False, box=None)
    config_table.add_column(style="bold cyan", width=3)
    config_table.add_column()

    config_table.add_row("1", "Quick Test Mode (3 URLs, fast)")
    config_table.add_row("2", "Standard Mode (10 URLs, balanced)")
    config_table.add_row("3", "Comprehensive Mode (20 URLs, thorough)")
    config_table.add_row("4", "Custom Configuration")

    console.print(config_table)

    config_choice = input("\nSelect configuration (1-4): ").strip()

    # Create config based on choice
    if config_choice == "1":
        config = ResearchConfig(test_mode=True, interactive_mode=False)
    elif config_choice == "2":
        config = ResearchConfig(max_urls_to_crawl=10, top_k_urls=10)
    elif config_choice == "3":
        config = ResearchConfig(max_urls_to_crawl=20, top_k_urls=20, max_urls_discovery=200)
    else:
        # Custom configuration
        config = ResearchConfig()
        config.test_mode = input("\nTest mode? (y/n): ").lower() == 'y'
        config.interactive_mode = input("Interactive mode (pause between steps)? (y/n): ").lower() == 'y'
        config.use_llm_enhancement = input("Use AI to enhance queries? (y/n): ").lower() == 'y'

        if not config.test_mode:
            try:
                config.max_urls_to_crawl = int(input("Max URLs to crawl (default 10): ") or "10")
                config.top_k_urls = int(input("Top K URLs to select (default 10): ") or "10")
            except ValueError:
                console.print("[yellow]Using default values[/yellow]")

    # Display example queries
    query_table = Table(title="\n📋 Example Queries", show_header=False, box=None)
    query_table.add_column(style="bold cyan", width=3)
    query_table.add_column()

    for i, q in enumerate(example_queries, 1):
        query_table.add_row(str(i), q)

    console.print(query_table)

    query_input = input("\nSelect a query (1-5) or enter your own: ").strip()

    if query_input.isdigit() and 1 <= int(query_input) <= len(example_queries):
        query = example_queries[int(query_input) - 1]
    else:
        query = query_input if query_input else example_queries[0]

    console.print(f"\n[bold cyan]📝 Selected Query:[/bold cyan] {query}")

    # Run the research pipeline
    result = await research_pipeline(query=query, config=config)

    # Display results
    formatted_output = format_research_output(result)
    # print(formatted_output)
    console.print(Panel.fit(
        formatted_output,
        title="🔬 Research Results",
        border_style="green"
    ))

    # Save results
    if config.save_json or config.save_markdown:
        json_path, md_path = await save_research_results(result, config)
        # print(f"\n✅ Results saved successfully!")
        if json_path:
            console.print(f"[green]JSON saved at:[/green] {json_path}")
        if md_path:
            console.print(f"[green]Markdown saved at:[/green] {md_path}")