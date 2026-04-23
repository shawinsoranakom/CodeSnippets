async def test_irrelevant_query_behavior():
    """Test how embedding strategy handles completely irrelevant queries"""
    console.print("\n[bold yellow]Test 8: Irrelevant Query Behavior[/bold yellow]")
    console.print("Testing embedding strategy with a query that has no semantic relevance to the content")

    # Test with irrelevant query on Python async documentation
    test_case = {
        "name": "Irrelevant Query on Python Docs",
        "url": "https://docs.python.org/3/library/asyncio.html",
        "query": "how to cook fried rice with vegetables"
    }

    console.print(f"\n[bold cyan]Testing: {test_case['name']}[/bold cyan]")
    console.print(f"URL: {test_case['url']} (Python async documentation)")
    console.print(f"Query: '{test_case['query']}' (completely irrelevant)")
    console.print("\n[dim]Expected behavior: Low confidence, high distances, no convergence[/dim]")

    # Configure embedding strategy
    config_emb = AdaptiveConfig(
        strategy="embedding",
        confidence_threshold=0.8,
        max_pages=9,
        top_k_links=3,
        min_gain_threshold=0.01,
        n_query_variations=5,
        embedding_min_relative_improvement=0.05,  # Lower threshold to see more iterations
        embedding_min_confidence_threshold=0.1  # Will stop if confidence < 10%
    )

    # Configure embeddings using the correct format
    config_emb.embedding_llm_config = {
        'provider': 'openai/gpt-4o-mini',
        'api_token': os.getenv('OPENAI_API_KEY'),
    }

    async with AsyncWebCrawler() as crawler:
        emb_crawler = AdaptiveCrawler(crawler=crawler, config=config_emb)

        start_time = time.time()
        state = await emb_crawler.digest(
            start_url=test_case['url'],
            query=test_case['query']
        )
        elapsed = time.time() - start_time

        # Analyze results
        console.print(f"\n[bold]Results after {elapsed:.1f} seconds:[/bold]")

        # Basic metrics
        total_pages = len(state.crawled_urls)
        final_confidence = emb_crawler.confidence

        console.print(f"\nPages crawled: {total_pages}")
        console.print(f"Final confidence: {final_confidence:.1%} {'✅' if emb_crawler.is_sufficient else '❌'}")

        # Distance metrics
        if 'avg_min_distance' in state.metrics:
            console.print(f"\n[yellow]Distance Metrics:[/yellow]")
            console.print(f"  Average minimum distance: {state.metrics['avg_min_distance']:.3f}")
            console.print(f"  Close neighbors (<0.3): {state.metrics.get('avg_close_neighbors', 0):.1f}")
            console.print(f"  Very close neighbors (<0.2): {state.metrics.get('avg_very_close_neighbors', 0):.1f}")

            # Interpret distances
            avg_dist = state.metrics['avg_min_distance']
            if avg_dist > 0.8:
                console.print(f"  [red]→ Very poor match (distance > 0.8)[/red]")
            elif avg_dist > 0.6:
                console.print(f"  [yellow]→ Poor match (distance > 0.6)[/yellow]")
            elif avg_dist > 0.4:
                console.print(f"  [blue]→ Moderate match (distance > 0.4)[/blue]")
            else:
                console.print(f"  [green]→ Good match (distance < 0.4)[/green]")

        # Show sample expanded queries
        if state.expanded_queries:
            console.print(f"\n[yellow]Sample Query Variations Generated:[/yellow]")
            for i, q in enumerate(state.expanded_queries[:3], 1):
                console.print(f"  {i}. {q}")

        # Show crawl progression
        console.print(f"\n[yellow]Crawl Progression:[/yellow]")
        for i, url in enumerate(state.crawl_order[:5], 1):
            console.print(f"  {i}. {url}")
        if len(state.crawl_order) > 5:
            console.print(f"  ... and {len(state.crawl_order) - 5} more")

        # Validation score
        if 'validation_confidence' in state.metrics:
            console.print(f"\n[yellow]Validation:[/yellow]")
            console.print(f"  Validation score: {state.metrics['validation_confidence']:.1%}")

        # Why it stopped
        if 'stopped_reason' in state.metrics:
            console.print(f"\n[yellow]Stopping Reason:[/yellow] {state.metrics['stopped_reason']}")
            if state.metrics.get('is_irrelevant', False):
                console.print("[red]→ Query and content are completely unrelated![/red]")
        elif total_pages >= config_emb.max_pages:
            console.print(f"\n[yellow]Stopping Reason:[/yellow] Reached max pages limit ({config_emb.max_pages})")

        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        if final_confidence < 0.2:
            console.print("[red]✗ As expected: Query is completely irrelevant to content[/red]")
            console.print("[green]✓ The embedding strategy correctly identified no semantic match[/green]")
        else:
            console.print(f"[yellow]⚠ Unexpected: Got {final_confidence:.1%} confidence for irrelevant query[/yellow]")
            console.print("[yellow]  This may indicate the query variations are too broad[/yellow]")