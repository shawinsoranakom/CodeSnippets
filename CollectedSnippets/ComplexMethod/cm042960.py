async def test_performance_scaling_lab( num_browsers: int = 10, pages_per_browser: int = 10):
    """Test performance with multiple browsers and pages.

    This test creates multiple browsers on different ports,
    spawns multiple pages per browser, and measures performance metrics.
    """
    print(f"\n{INFO}========== Testing Performance Scaling =========={RESET}")

    # Configuration parameters
    num_browsers = num_browsers
    pages_per_browser = pages_per_browser
    total_pages = num_browsers * pages_per_browser
    base_port = 9222

    # Set up a measuring mechanism for memory
    import psutil
    import gc

    # Force garbage collection before starting
    gc.collect()
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # in MB
    peak_memory = initial_memory

    # Report initial configuration
    print(
        f"{INFO}Test configuration: {num_browsers} browsers × {pages_per_browser} pages = {total_pages} total crawls{RESET}"
    )

    # List to track managers
    managers: List[BrowserManager] = []
    all_pages = []

    # Get crawl4ai home directory
    crawl4ai_home = os.path.expanduser("~/.crawl4ai")
    temp_dir = os.path.join(crawl4ai_home, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Create all managers but don't start them yet
    manager_configs = []
    for i in range(num_browsers):
        port = base_port + i
        browser_config = BrowserConfig(
            browser_mode="builtin",
            headless=True,
            debugging_port=port,
            user_data_dir=os.path.join(temp_dir, f"browser_profile_{i}"),
        )
        manager = BrowserManager(browser_config=browser_config, logger=logger)
        manager.strategy.shutting_down = True
        manager_configs.append((manager, i, port))

    # Define async function to start a single manager
    async def start_manager(manager, index, port):
        try:
            await manager.start()
            return manager
        except Exception as e:
            print(
                f"{ERROR}Failed to start browser {index + 1} on port {port}: {str(e)}{RESET}"
            )
            return None

    # Start all managers in parallel
    start_tasks = [
        start_manager(manager, i, port) for manager, i, port in manager_configs
    ]
    started_managers = await asyncio.gather(*start_tasks)

    # Filter out None values (failed starts) and add to managers list
    managers = [m for m in started_managers if m is not None]

    if len(managers) == 0:
        print(f"{ERROR}All browser managers failed to start. Aborting test.{RESET}")
        return False

    if len(managers) < num_browsers:
        print(
            f"{WARNING}Only {len(managers)} out of {num_browsers} browser managers started successfully{RESET}"
        )

    # Create pages for each browser
    for i, manager in enumerate(managers):
        try:
            pages = await manager.get_pages(CrawlerRunConfig(), count=pages_per_browser)
            all_pages.extend(pages)
        except Exception as e:
            print(f"{ERROR}Failed to create pages for browser {i + 1}: {str(e)}{RESET}")

    # Check memory after page creation
    gc.collect()
    current_memory = process.memory_info().rss / 1024 / 1024
    peak_memory = max(peak_memory, current_memory)

    # Ask for confirmation before loading
    confirmation = input(
        f"{WARNING}Do you want to proceed with loading pages? (y/n): {RESET}"
    )
    # Step 1: Create and start multiple browser managers in parallel
    start_time = time.time()

    if confirmation.lower() == "y":
        load_start_time = time.time()

        # Function to load a single page
        async def load_page(page_ctx, index):
            page, _ = page_ctx
            try:
                await page.goto(f"https://example.com/page{index}", timeout=30000)
                title = await page.title()
                return title
            except Exception as e:
                return f"Error: {str(e)}"

        # Load all pages concurrently
        load_tasks = [load_page(page_ctx, i) for i, page_ctx in enumerate(all_pages)]
        load_results = await asyncio.gather(*load_tasks, return_exceptions=True)

        # Count successes and failures
        successes = sum(
            1 for r in load_results if isinstance(r, str) and not r.startswith("Error")
        )
        failures = len(load_results) - successes

        load_time = time.time() - load_start_time
        total_test_time = time.time() - start_time

        # Check memory after loading (peak memory)
        gc.collect()
        current_memory = process.memory_info().rss / 1024 / 1024
        peak_memory = max(peak_memory, current_memory)

        # Calculate key metrics
        memory_per_page = peak_memory / successes if successes > 0 else 0
        time_per_crawl = total_test_time / successes if successes > 0 else 0
        crawls_per_second = successes / total_test_time if total_test_time > 0 else 0
        crawls_per_minute = crawls_per_second * 60
        crawls_per_hour = crawls_per_minute * 60

        # Print simplified performance summary
        from rich.console import Console
        from rich.table import Table

        console = Console()

        # Create a simple summary table
        table = Table(title="CRAWL4AI PERFORMANCE SUMMARY")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Crawls Completed", f"{successes}")
        table.add_row("Total Time", f"{total_test_time:.2f} seconds")
        table.add_row("Time Per Crawl", f"{time_per_crawl:.2f} seconds")
        table.add_row("Crawling Speed", f"{crawls_per_second:.2f} crawls/second")
        table.add_row("Projected Rate (1 minute)", f"{crawls_per_minute:.0f} crawls")
        table.add_row("Projected Rate (1 hour)", f"{crawls_per_hour:.0f} crawls")
        table.add_row("Peak Memory Usage", f"{peak_memory:.2f} MB")
        table.add_row("Memory Per Crawl", f"{memory_per_page:.2f} MB")

        # Display the table
        console.print(table)

    # Ask confirmation before cleanup
    confirmation = input(
        f"{WARNING}Do you want to proceed with cleanup? (y/n): {RESET}"
    )
    if confirmation.lower() != "y":
        print(f"{WARNING}Cleanup aborted by user{RESET}")
        return False

    # Close all pages
    for page, _ in all_pages:
        try:
            await page.close()
        except:
            pass

    # Close all managers
    for manager in managers:
        try:
            await manager.close()
        except:
            pass

    # Remove the temp directory
    import shutil

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    return True