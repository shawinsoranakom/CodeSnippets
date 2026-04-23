async def grid_search_optimal_configuration(total_urls=50):
    """Perform a grid search to find the optimal balance between number of browsers and pages per browser.

    This function tests different combinations of browser count and pages per browser,
    while keeping the total number of URLs constant. It measures performance metrics
    for each configuration to find the "sweet spot" that provides the best speed 
    with reasonable memory usage.

    Args:
        total_urls: Total number of URLs to crawl (default: 50)
    """
    logger.info(f"=== GRID SEARCH FOR OPTIMAL CRAWLING CONFIGURATION ({total_urls} URLs) ===", tag="TEST")

    # Generate test URLs once
    urls = [f"https://example.com/page_{i}" for i in range(total_urls)]

    # Define grid search configurations
    # We'll use more flexible approach: test all browser counts from 1 to min(20, total_urls)
    # and distribute pages evenly (some browsers may have 1 more page than others)
    configurations = []

    # Maximum number of browsers to test
    max_browsers_to_test = min(20, total_urls)

    # Try configurations with 1 to max_browsers_to_test browsers
    for num_browsers in range(1, max_browsers_to_test + 1):
        base_pages_per_browser = total_urls // num_browsers
        remainder = total_urls % num_browsers

        # Generate exact page distribution array
        if remainder > 0:
            # First 'remainder' browsers get one more page
            page_distribution = [base_pages_per_browser + 1] * remainder + [base_pages_per_browser] * (num_browsers - remainder)
            pages_distribution = f"{base_pages_per_browser+1} pages × {remainder} browsers, {base_pages_per_browser} pages × {num_browsers - remainder} browsers"
        else:
            # All browsers get the same number of pages
            page_distribution = [base_pages_per_browser] * num_browsers
            pages_distribution = f"{base_pages_per_browser} pages × {num_browsers} browsers"

        # Format the distribution as a tuple string like (4, 4, 3, 3)
        distribution_str = str(tuple(page_distribution))

        configurations.append((num_browsers, base_pages_per_browser, pages_distribution, page_distribution, distribution_str))

    # Track results
    results = []

    # Test each configuration
    for num_browsers, pages_per_browser, pages_distribution, page_distribution, distribution_str in configurations:
        logger.info("-" * 80, tag="TEST")
        logger.info(f"Testing configuration: {num_browsers} browsers with distribution: {distribution_str}", tag="TEST")
        logger.info(f"Details: {pages_distribution}", tag="TEST")
        # Sleep a bit for randomness
        await asyncio.sleep(0.5)

        try:
            # Import psutil for memory tracking
            try:
                import psutil
                process = psutil.Process()
                initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
            except ImportError:
                logger.warning("psutil not available, memory metrics will not be tracked", tag="TEST")
                initial_memory = 0

            # Create and start browser managers
            managers = []
            start_time = time.time()

            # Start all browsers in parallel
            start_tasks = []
            for i in range(num_browsers):
                browser_config = BrowserConfig(
                    headless=True
                )
                manager = BrowserManager(browser_config=browser_config, logger=logger)
                start_tasks.append(manager.start())
                managers.append(manager)

            await asyncio.gather(*start_tasks)
            browser_startup_time = time.time() - start_time

            # Measure memory after browser startup
            if initial_memory > 0:
                browser_memory = process.memory_info().rss / (1024 * 1024) - initial_memory
            else:
                browser_memory = 0

            # Distribute URLs among managers using the exact page distribution
            urls_per_manager = {}
            total_assigned = 0

            for i, manager in enumerate(managers):
                if i < len(page_distribution):
                    # Get the exact number of pages for this browser from our distribution
                    manager_pages = page_distribution[i]

                    # Get the URL slice for this manager
                    start_idx = total_assigned
                    end_idx = start_idx + manager_pages
                    urls_per_manager[manager] = urls[start_idx:end_idx]
                    total_assigned += manager_pages
                else:
                    # If we have more managers than our distribution (should never happen)
                    urls_per_manager[manager] = []

            # Use the more efficient approach (pre-created pages)
            logger.info("Running page crawling test...", tag="TEST")
            crawl_start_time = time.time()

            # Get all pages upfront for each manager
            all_pages = []
            for manager, manager_urls in urls_per_manager.items():
                if not manager_urls:  # Skip managers with no URLs
                    continue
                crawler_config = CrawlerRunConfig()
                pages = await manager.get_pages(crawler_config, count=len(manager_urls))
                all_pages.extend(zip(pages, manager_urls))

            # Measure memory after page creation
            if initial_memory > 0:
                pages_memory = process.memory_info().rss / (1024 * 1024) - browser_memory - initial_memory
            else:
                pages_memory = 0

            # Function to crawl a URL with a pre-created page
            async def fetch_title(page_ctx, url):
                page, _ = page_ctx
                try:
                    await page.goto(url)
                    title = await page.title()
                    return title
                finally:
                    await page.close()

            # Use the pre-created pages to fetch titles in parallel
            tasks = [fetch_title(page_ctx, url) for page_ctx, url in all_pages]
            crawl_results = await asyncio.gather(*tasks)

            crawl_time = time.time() - crawl_start_time
            total_time = time.time() - start_time

            # Final memory measurement
            if initial_memory > 0:
                peak_memory = max(browser_memory + pages_memory, process.memory_info().rss / (1024 * 1024) - initial_memory)
            else:
                peak_memory = 0

            # Close all managers
            for manager in managers:
                await manager.close()

            # Calculate metrics
            pages_per_second = total_urls / crawl_time

            # Store result metrics
            result = {
                "num_browsers": num_browsers,
                "pages_per_browser": pages_per_browser,
                "page_distribution": page_distribution,
                "distribution_str": distribution_str,
                "total_urls": total_urls,
                "browser_startup_time": browser_startup_time,
                "crawl_time": crawl_time,
                "total_time": total_time,
                "browser_memory": browser_memory,
                "pages_memory": pages_memory,
                "peak_memory": peak_memory,
                "pages_per_second": pages_per_second,
                # Calculate efficiency score (higher is better)
                # This balances speed vs memory usage
                "efficiency_score": pages_per_second / (peak_memory + 1) if peak_memory > 0 else pages_per_second,
            }

            results.append(result)

            # Log the results
            logger.info(f"Browser startup: {browser_startup_time:.2f}s", tag="TEST")
            logger.info(f"Crawl time: {crawl_time:.2f}s", tag="TEST")
            logger.info(f"Total time: {total_time:.2f}s", tag="TEST")
            logger.info(f"Performance: {pages_per_second:.1f} pages/second", tag="TEST")

            if peak_memory > 0:
                logger.info(f"Browser memory: {browser_memory:.1f}MB", tag="TEST")
                logger.info(f"Pages memory: {pages_memory:.1f}MB", tag="TEST")
                logger.info(f"Peak memory: {peak_memory:.1f}MB", tag="TEST")
                logger.info(f"Efficiency score: {result['efficiency_score']:.6f}", tag="TEST")

        except Exception as e:
            logger.error(f"Error testing configuration: {str(e)}", tag="TEST")
            import traceback
            traceback.print_exc()

            # Clean up
            for manager in managers:
                try:
                    await manager.close()
                except:
                    pass

    # Print summary of all configurations
    logger.info("=" * 100, tag="TEST")
    logger.info("GRID SEARCH RESULTS SUMMARY", tag="TEST")
    logger.info("=" * 100, tag="TEST")

    # Rank configurations by efficiency score
    ranked_results = sorted(results, key=lambda x: x["efficiency_score"], reverse=True)

    # Also determine rankings by different metrics
    fastest = sorted(results, key=lambda x: x["crawl_time"])[0]
    lowest_memory = sorted(results, key=lambda x: x["peak_memory"] if x["peak_memory"] > 0 else float('inf'))[0]
    most_efficient = ranked_results[0]

    # Print top performers by category
    logger.info("🏆 TOP PERFORMERS BY CATEGORY:", tag="TEST")
    logger.info(f"⚡ Fastest: {fastest['num_browsers']} browsers × ~{fastest['pages_per_browser']} pages " + 
                f"({fastest['crawl_time']:.2f}s, {fastest['pages_per_second']:.1f} pages/s)", tag="TEST")

    if lowest_memory["peak_memory"] > 0:
        logger.info(f"💾 Lowest memory: {lowest_memory['num_browsers']} browsers × ~{lowest_memory['pages_per_browser']} pages " +
                    f"({lowest_memory['peak_memory']:.1f}MB)", tag="TEST")

    logger.info(f"🌟 Most efficient: {most_efficient['num_browsers']} browsers × ~{most_efficient['pages_per_browser']} pages " +
                f"(score: {most_efficient['efficiency_score']:.6f})", tag="TEST")

    # Print result table header
    logger.info("\n📊 COMPLETE RANKING TABLE (SORTED BY EFFICIENCY SCORE):", tag="TEST")
    logger.info("-" * 120, tag="TEST")

    # Define table header
    header = f"{'Rank':<5} | {'Browsers':<8} | {'Distribution':<55} | {'Total Time(s)':<12} | {'Speed(p/s)':<12} | {'Memory(MB)':<12} | {'Efficiency':<10} | {'Notes'}"
    logger.info(header, tag="TEST")
    logger.info("-" * 120, tag="TEST")

    # Print each configuration in ranked order
    for rank, result in enumerate(ranked_results, 1):
        # Add special notes for top performers
        notes = []
        if result == fastest:
            notes.append("⚡ Fastest")
        if result == lowest_memory:
            notes.append("💾 Lowest Memory")
        if result == most_efficient:
            notes.append("🌟 Most Efficient")

        notes_str = " | ".join(notes) if notes else ""

        # Format memory if available
        memory_str = f"{result['peak_memory']:.1f}" if result['peak_memory'] > 0 else "N/A"

        # Get the distribution string
        dist_str = result.get('distribution_str', str(tuple([result['pages_per_browser']] * result['num_browsers'])))

        # Build the row
        row = f"{rank:<5} | {result['num_browsers']:<8} | {dist_str:<55} | {result['total_time']:.2f}s{' ':<7} | "
        row += f"{result['pages_per_second']:.2f}{' ':<6} | {memory_str}{' ':<6} | {result['efficiency_score']:.4f}{' ':<4} | {notes_str}"

        logger.info(row, tag="TEST")

    logger.info("-" * 120, tag="TEST")

    # Generate visualization if matplotlib is available
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        # Extract data for plotting from ranked results
        browser_counts = [r["num_browsers"] for r in ranked_results]
        efficiency_scores = [r["efficiency_score"] for r in ranked_results]
        crawl_times = [r["crawl_time"] for r in ranked_results]
        total_times = [r["total_time"] for r in ranked_results]

        # Filter results with memory data
        memory_results = [r for r in ranked_results if r["peak_memory"] > 0]
        memory_browser_counts = [r["num_browsers"] for r in memory_results]
        peak_memories = [r["peak_memory"] for r in memory_results]

        # Create figure with clean design
        plt.figure(figsize=(14, 12), facecolor='white')
        plt.style.use('ggplot')

        # Create grid for subplots
        gs = plt.GridSpec(3, 1, height_ratios=[1, 1, 1], hspace=0.3)

        # Plot 1: Efficiency Score (higher is better)
        ax1 = plt.subplot(gs[0])
        bar_colors = ['#3498db'] * len(browser_counts)

        # Highlight the most efficient
        most_efficient_idx = browser_counts.index(most_efficient["num_browsers"])
        bar_colors[most_efficient_idx] = '#e74c3c'  # Red for most efficient

        bars = ax1.bar(range(len(browser_counts)), efficiency_scores, color=bar_colors)
        ax1.set_xticks(range(len(browser_counts)))
        ax1.set_xticklabels([f"{bc}" for bc in browser_counts], rotation=45)
        ax1.set_xlabel('Number of Browsers')
        ax1.set_ylabel('Efficiency Score (higher is better)')
        ax1.set_title('Browser Configuration Efficiency (higher is better)')

        # Add value labels on top of bars
        for bar, score in zip(bars, efficiency_scores):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02*max(efficiency_scores),
                    f'{score:.3f}', ha='center', va='bottom', rotation=90, fontsize=8)

        # Highlight best configuration
        ax1.text(0.02, 0.90, f"🌟 Most Efficient: {most_efficient['num_browsers']} browsers with ~{most_efficient['pages_per_browser']} pages",
                transform=ax1.transAxes, fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3))

        # Plot 2: Time Performance
        ax2 = plt.subplot(gs[1])

        # Plot both total time and crawl time
        ax2.plot(browser_counts, crawl_times, 'bo-', label='Crawl Time (s)', linewidth=2)
        ax2.plot(browser_counts, total_times, 'go--', label='Total Time (s)', linewidth=2, alpha=0.6)

        # Mark the fastest configuration
        fastest_idx = browser_counts.index(fastest["num_browsers"])
        ax2.plot(browser_counts[fastest_idx], crawl_times[fastest_idx], 'ro', ms=10, 
                label=f'Fastest: {fastest["num_browsers"]} browsers')

        ax2.set_xlabel('Number of Browsers')
        ax2.set_ylabel('Time (seconds)')
        ax2.set_title(f'Time Performance for {total_urls} URLs by Browser Count')
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.legend(loc='upper right')

        # Plot pages per second on second y-axis
        pages_per_second = [total_urls/t for t in crawl_times]
        ax2_twin = ax2.twinx()
        ax2_twin.plot(browser_counts, pages_per_second, 'r^--', label='Pages/second', alpha=0.5)
        ax2_twin.set_ylabel('Pages per second')

        # Add note about the fastest configuration
        ax2.text(0.02, 0.90, f"⚡ Fastest: {fastest['num_browsers']} browsers with ~{fastest['pages_per_browser']} pages" +
                f"\n   {fastest['crawl_time']:.2f}s ({fastest['pages_per_second']:.1f} pages/s)",
                transform=ax2.transAxes, fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.3))

        # Plot 3: Memory Usage (if available)
        if memory_results:
            ax3 = plt.subplot(gs[2])

            # Prepare data for grouped bar chart
            memory_per_browser = [m/n for m, n in zip(peak_memories, memory_browser_counts)]
            memory_per_page = [m/(n*p) for m, n, p in zip(
                [r["peak_memory"] for r in memory_results],
                [r["num_browsers"] for r in memory_results],
                [r["pages_per_browser"] for r in memory_results])]

            x = np.arange(len(memory_browser_counts))
            width = 0.35

            # Create grouped bars
            ax3.bar(x - width/2, peak_memories, width, label='Total Memory (MB)', color='#9b59b6')
            ax3.bar(x + width/2, memory_per_browser, width, label='Memory per Browser (MB)', color='#3498db')

            # Configure axis
            ax3.set_xticks(x)
            ax3.set_xticklabels([f"{bc}" for bc in memory_browser_counts], rotation=45)
            ax3.set_xlabel('Number of Browsers')
            ax3.set_ylabel('Memory (MB)')
            ax3.set_title('Memory Usage by Browser Configuration')
            ax3.legend(loc='upper left')
            ax3.grid(True, linestyle='--', alpha=0.7)

            # Add second y-axis for memory per page
            ax3_twin = ax3.twinx()
            ax3_twin.plot(x, memory_per_page, 'ro-', label='Memory per Page (MB)')
            ax3_twin.set_ylabel('Memory per Page (MB)')

            # Get lowest memory configuration
            lowest_memory_idx = memory_browser_counts.index(lowest_memory["num_browsers"])

            # Add note about lowest memory configuration
            ax3.text(0.02, 0.90, f"💾 Lowest Memory: {lowest_memory['num_browsers']} browsers with ~{lowest_memory['pages_per_browser']} pages" +
                    f"\n   {lowest_memory['peak_memory']:.1f}MB ({lowest_memory['peak_memory']/total_urls:.2f}MB per page)",
                    transform=ax3.transAxes, fontsize=12, verticalalignment='top',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.3))

        # Add overall title
        plt.suptitle(f'Browser Scaling Grid Search Results for {total_urls} URLs', fontsize=16, y=0.98)

        # Add timestamp and info at the bottom
        plt.figtext(0.5, 0.01, f"Generated by Crawl4AI at {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                   ha="center", fontsize=10, style='italic')

        # Get current directory and save the figure there
        import os
        __current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(__current_file)
        output_file = os.path.join(current_dir, 'browser_scaling_grid_search.png')

        # Adjust layout and save figure with high DPI
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        plt.savefig(output_file, dpi=200, bbox_inches='tight')
        logger.success(f"Visualization saved to {output_file}", tag="TEST")

    except ImportError:
        logger.warning("matplotlib not available, skipping visualization", tag="TEST")

    return most_efficient["num_browsers"], most_efficient["pages_per_browser"]