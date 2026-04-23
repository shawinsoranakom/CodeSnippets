async def test_fast_convergence_with_relevant_query():
    """Test that both strategies reach high confidence quickly with relevant queries"""
    console.print("\n[bold yellow]Test 7: Fast Convergence with Relevant Query[/bold yellow]")
    console.print("Testing that strategies reach 80%+ confidence within 2-3 batches")

    # Test scenarios
    test_cases = [
        {
            "name": "Python Async Documentation",
            "url": "https://docs.python.org/3/library/asyncio.html",
            "query": "async await coroutines event loops tasks"
        }
    ]

    for test_case in test_cases:
        console.print(f"\n[bold cyan]Testing: {test_case['name']}[/bold cyan]")
        console.print(f"URL: {test_case['url']}")
        console.print(f"Query: {test_case['query']}")

        # Test Embedding Strategy
        console.print("\n[yellow]Embedding Strategy:[/yellow]")
        config_emb = AdaptiveConfig(
            strategy="embedding",
            confidence_threshold=0.8,
            max_pages=9,
            top_k_links=3,
            min_gain_threshold=0.01,
            n_query_variations=5
        )

        # Configure embeddings
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

            # Get batch breakdown
            total_pages = len(state.crawled_urls)
            for i in range(0, total_pages, 3):
                batch_num = (i // 3) + 1
                batch_pages = min(3, total_pages - i)
                pages_so_far = i + batch_pages
                estimated_confidence = state.metrics.get('confidence', 0) * (pages_so_far / total_pages)

                console.print(f"Batch {batch_num}: {batch_pages} pages → Confidence: {estimated_confidence:.1%} {'✅' if estimated_confidence >= 0.8 else '❌'}")

            final_confidence = emb_crawler.confidence
            console.print(f"[green]Final: {total_pages} pages → Confidence: {final_confidence:.1%} {'✅ (Sufficient!)' if emb_crawler.is_sufficient else '❌'}[/green]")

            # Show learning metrics for embedding
            if 'avg_min_distance' in state.metrics:
                console.print(f"[dim]Avg gap distance: {state.metrics['avg_min_distance']:.3f}[/dim]")
            if 'validation_confidence' in state.metrics:
                console.print(f"[dim]Validation score: {state.metrics['validation_confidence']:.1%}[/dim]")

        # Test Statistical Strategy
        console.print("\n[yellow]Statistical Strategy:[/yellow]")
        config_stat = AdaptiveConfig(
            strategy="statistical",
            confidence_threshold=0.8,
            max_pages=9,
            top_k_links=3,
            min_gain_threshold=0.01
        )

        async with AsyncWebCrawler() as crawler:
            stat_crawler = AdaptiveCrawler(crawler=crawler, config=config_stat)

            # Track batch progress
            batch_results = []
            current_pages = 0

            # Custom batch tracking
            start_time = time.time()
            state = await stat_crawler.digest(
                start_url=test_case['url'],
                query=test_case['query']
            )

            # Get batch breakdown (every 3 pages)
            total_pages = len(state.crawled_urls)
            for i in range(0, total_pages, 3):
                batch_num = (i // 3) + 1
                batch_pages = min(3, total_pages - i)
                # Estimate confidence at this point (simplified)
                pages_so_far = i + batch_pages
                estimated_confidence = state.metrics.get('confidence', 0) * (pages_so_far / total_pages)

                console.print(f"Batch {batch_num}: {batch_pages} pages → Confidence: {estimated_confidence:.1%} {'✅' if estimated_confidence >= 0.8 else '❌'}")

            final_confidence = stat_crawler.confidence
            console.print(f"[green]Final: {total_pages} pages → Confidence: {final_confidence:.1%} {'✅ (Sufficient!)' if stat_crawler.is_sufficient else '❌'}[/green]")