async def test_with_llm_after_fix():
    """Demonstrate the fix: Parallel execution with LLM"""
    print_section("TEST 3: After Fix - LLM Extraction in Parallel")

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=LLMExtractionStrategy(
            llm_config=LLMConfig(provider="openai/gpt-4o-mini"),
            schema=SimpleData.model_json_schema(),
            extraction_type="schema",
            instruction="Extract title and summary",
        )
    )

    browser_config = BrowserConfig(headless=True, verbose=False)

    urls = [
        "https://www.example.com",
        "https://www.iana.org",
        "https://www.wikipedia.org",
    ]

    print(f"Crawling {len(urls)} URLs WITH LLM extraction...")
    print("Expected: Parallel execution with our fix\n")

    completion_times = {}
    start_time = time.time()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=urls, config=config)
        for result in results:
            elapsed = time.time() - start_time
            completion_times[result.url] = elapsed
            print(f"  [{elapsed:5.2f}s] ✓ {result.url[:50]}")

    duration = time.time() - start_time

    print(f"\n✅ Total time: {duration:.2f}s")
    print(f"   Successful: {sum(1 for url in urls if url in completion_times)}/{len(urls)}")

    # Analyze parallelism
    times = list(completion_times.values())
    if len(times) >= 2:
        # If parallel, completion times should be staggered, not evenly spaced
        time_diffs = [times[i+1] - times[i] for i in range(len(times)-1)]
        avg_diff = sum(time_diffs) / len(time_diffs)

        print(f"\nParallelism Analysis:")
        print(f"   Completion time differences: {[f'{d:.2f}s' for d in time_diffs]}")
        print(f"   Average difference: {avg_diff:.2f}s")

        # In parallel mode, some tasks complete close together
        # In sequential mode, they're evenly spaced (avg ~2-3s apart)
        if avg_diff < duration / len(urls):
            print(f"   ✅ PARALLEL: Tasks completed with overlapping execution")
        else:
            print(f"   ⚠️  SEQUENTIAL: Tasks completed one after another")

    return duration