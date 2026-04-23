async def find_optimal_browser_config(total_urls=50, verbose=True, rate_limit_delay=0.2):
    """Find optimal browser configuration for crawling a specific number of URLs.

    Args:
        total_urls: Number of URLs to crawl
        verbose: Whether to print progress
        rate_limit_delay: Delay between page loads to avoid rate limiting

    Returns:
        dict: Contains fastest, lowest_memory, and optimal configurations
    """
    if verbose:
        print(f"\n=== Finding optimal configuration for crawling {total_urls} URLs ===\n")

    # Generate test URLs with timestamp to avoid caching
    timestamp = int(time.time())
    urls = [f"https://example.com/page_{i}?t={timestamp}" for i in range(total_urls)]

    # Limit browser configurations to test (1 browser to max 10)
    max_browsers = min(10, total_urls)
    configs_to_test = []

    # Generate configurations (browser count, pages distribution)
    for num_browsers in range(1, max_browsers + 1):
        base_pages = total_urls // num_browsers
        remainder = total_urls % num_browsers

        # Create distribution array like [3, 3, 2, 2] (some browsers get one more page)
        if remainder > 0:
            distribution = [base_pages + 1] * remainder + [base_pages] * (num_browsers - remainder)
        else:
            distribution = [base_pages] * num_browsers

        configs_to_test.append((num_browsers, distribution))

    results = []

    # Test each configuration
    for browser_count, page_distribution in configs_to_test:
        if verbose:
            print(f"Testing {browser_count} browsers with distribution {tuple(page_distribution)}")

        try:
            # Track memory if possible
            try:
                import psutil
                process = psutil.Process()
                start_memory = process.memory_info().rss / (1024 * 1024)  # MB
            except ImportError:
                if verbose: 
                    print("Memory tracking not available (psutil not installed)")
                start_memory = 0

            # Start browsers in parallel
            managers = []
            start_tasks = []
            start_time = time.time()

            for i in range(browser_count):
                config = BrowserConfig(headless=True)
                manager = BrowserManager(browser_config=config, logger=logger)
                start_tasks.append(manager.start())
                managers.append(manager)

            await asyncio.gather(*start_tasks)

            # Distribute URLs among browsers
            urls_per_manager = {}
            url_index = 0

            for i, manager in enumerate(managers):
                pages_for_this_browser = page_distribution[i]
                end_index = url_index + pages_for_this_browser
                urls_per_manager[manager] = urls[url_index:end_index]
                url_index = end_index

            # Create pages for each browser
            all_pages = []
            for manager, manager_urls in urls_per_manager.items():
                if not manager_urls:
                    continue
                pages = await manager.get_pages(CrawlerRunConfig(), count=len(manager_urls))
                all_pages.extend(zip(pages, manager_urls))

            # Crawl pages with delay to avoid rate limiting
            async def crawl_page(page_ctx, url):
                page, _ = page_ctx
                try:
                    await page.goto(url)
                    if rate_limit_delay > 0:
                        await asyncio.sleep(rate_limit_delay)
                    title = await page.title()
                    return title
                finally:
                    await page.close()

            crawl_start = time.time()
            crawl_tasks = [crawl_page(page_ctx, url) for page_ctx, url in all_pages]
            await asyncio.gather(*crawl_tasks)
            crawl_time = time.time() - crawl_start
            total_time = time.time() - start_time

            # Measure final memory usage
            if start_memory > 0:
                end_memory = process.memory_info().rss / (1024 * 1024)
                memory_used = end_memory - start_memory
            else:
                memory_used = 0

            # Close all browsers
            for manager in managers:
                await manager.close()

            # Calculate metrics
            pages_per_second = total_urls / crawl_time

            # Calculate efficiency score (higher is better)
            # This balances speed vs memory
            if memory_used > 0:
                efficiency = pages_per_second / (memory_used + 1)
            else:
                efficiency = pages_per_second

            # Store result
            result = {
                "browser_count": browser_count,
                "distribution": tuple(page_distribution),
                "crawl_time": crawl_time,
                "total_time": total_time,
                "memory_used": memory_used,
                "pages_per_second": pages_per_second, 
                "efficiency": efficiency
            }

            results.append(result)

            if verbose:
                print(f"  ✓ Crawled {total_urls} pages in {crawl_time:.2f}s ({pages_per_second:.1f} pages/sec)")
                if memory_used > 0:
                    print(f"  ✓ Memory used: {memory_used:.1f}MB ({memory_used/total_urls:.1f}MB per page)")
                print(f"  ✓ Efficiency score: {efficiency:.4f}")

        except Exception as e:
            if verbose:
                print(f"  ✗ Error: {str(e)}")

            # Clean up
            for manager in managers:
                try:
                    await manager.close()
                except:
                    pass

    # If no successful results, return None
    if not results:
        return None

    # Find best configurations
    fastest = sorted(results, key=lambda x: x["crawl_time"])[0]

    # Only consider memory if available
    memory_results = [r for r in results if r["memory_used"] > 0]
    if memory_results:
        lowest_memory = sorted(memory_results, key=lambda x: x["memory_used"])[0]
    else:
        lowest_memory = fastest

    # Find most efficient (balanced speed vs memory)
    optimal = sorted(results, key=lambda x: x["efficiency"], reverse=True)[0]

    # Print summary
    if verbose:
        print("\n=== OPTIMAL CONFIGURATIONS ===")
        print(f"⚡ Fastest: {fastest['browser_count']} browsers {fastest['distribution']}")
        print(f"   {fastest['crawl_time']:.2f}s, {fastest['pages_per_second']:.1f} pages/sec")

        print(f"💾 Memory-efficient: {lowest_memory['browser_count']} browsers {lowest_memory['distribution']}")
        if lowest_memory["memory_used"] > 0:
            print(f"   {lowest_memory['memory_used']:.1f}MB, {lowest_memory['memory_used']/total_urls:.2f}MB per page")

        print(f"🌟 Balanced optimal: {optimal['browser_count']} browsers {optimal['distribution']}")
        print(f"   {optimal['crawl_time']:.2f}s, {optimal['pages_per_second']:.1f} pages/sec, score: {optimal['efficiency']:.4f}")

    return {
        "fastest": fastest,
        "lowest_memory": lowest_memory,
        "optimal": optimal,
        "all_configs": results
    }