async def research_pipeline(
    query: str,
    config: ResearchConfig
) -> ResearchResult:
    """
    Main research pipeline orchestrator with configurable settings
    """
    start_time = datetime.now()

    # Display pipeline header
    header = Panel(
        f"[bold cyan]Research Pipeline[/bold cyan]\n\n"
        f"[dim]Domain:[/dim] {config.domain}\n"
        f"[dim]Mode:[/dim] {'Test' if config.test_mode else 'Production'}\n"
        f"[dim]Interactive:[/dim] {'Yes' if config.interactive_mode else 'No'}",
        title="🚀 Starting",
        border_style="cyan"
    )
    console.print(header)

    # Step 1: Enhance query (optional)
    console.print(f"\n[bold cyan]📝 Step 1: Query Processing[/bold cyan]")
    if config.interactive_mode:
        await wait_for_user()

    if config.use_llm_enhancement:
        research_query = await enhance_query_with_llm(query)
    else:
        research_query = ResearchQuery(
            original_query=query,
            enhanced_query=query,
            search_patterns=tokenize_query_to_patterns(query),
            timestamp=datetime.now().isoformat()
        )

    console.print(f"   [green]✅ Query ready:[/green] {research_query.enhanced_query or query}")

    # Step 2: Discover URLs
    console.print(f"\n[bold cyan]🔍 Step 2: URL Discovery[/bold cyan]")
    if config.interactive_mode:
        await wait_for_user()

    discovered_urls = await discover_urls(
        domain=config.domain,
        query=research_query.enhanced_query or query,
        config=config
    )

    if not discovered_urls:
        return ResearchResult(
            query=research_query,
            discovered_urls=[],
            crawled_content=[],
            synthesis="No relevant URLs found for the given query.",
            citations=[],
            metadata={'duration': str(datetime.now() - start_time)}
        )

    console.print(f"   [green]✅ Found {len(discovered_urls)} relevant URLs[/green]")

    # Step 3: Crawl selected URLs
    console.print(f"\n[bold cyan]🕷️ Step 3: Content Crawling[/bold cyan]")
    if config.interactive_mode:
        await wait_for_user()

    crawled_content = await crawl_selected_urls(
        urls=discovered_urls,
        query=research_query.enhanced_query or query,
        config=config
    )

    console.print(f"   [green]✅ Successfully crawled {len(crawled_content)} pages[/green]")

    # Step 4: Generate synthesis
    console.print(f"\n[bold cyan]🤖 Step 4: Synthesis Generation[/bold cyan]")
    if config.interactive_mode:
        await wait_for_user()

    synthesis, citations = await generate_research_synthesis(
        query=research_query.enhanced_query or query,
        crawled_content=crawled_content
    )

    console.print(f"   [green]✅ Generated synthesis with {len(citations)} citations[/green]")

    # Step 5: Create result
    result = ResearchResult(
        query=research_query,
        discovered_urls=discovered_urls,
        crawled_content=crawled_content,
        synthesis=synthesis,
        citations=citations,
        metadata={
            'duration': str(datetime.now() - start_time),
            'domain': config.domain,
            'timestamp': datetime.now().isoformat(),
            'config': asdict(config)
        }
    )

    duration = datetime.now() - start_time
    console.print(f"\n[bold green]✅ Research completed in {duration}[/bold green]")

    return result