async def test_multi_browser_scaling(num_browsers=3, pages_per_browser=5):
    """Test performance with multiple browsers and pages per browser.
    Compares two approaches:
    1. On-demand page creation (get_page + gather)
    2. Pre-created pages (get_pages + gather)
    """
    logger.info(f"Testing multi-browser scaling with {num_browsers} browsers × {pages_per_browser} pages", tag="TEST")

    # Generate test URLs
    total_pages = num_browsers * pages_per_browser
    urls = [f"https://example.com/page_{i}" for i in range(total_pages)]

    # Create browser managers
    managers = []
    base_port = 9222

    try:
        # Start all browsers in parallel
        start_tasks = []
        for i in range(num_browsers):
            browser_config = BrowserConfig(
                headless=True  # Using default browser mode like in test_parallel_approaches_comparison
            )
            manager = BrowserManager(browser_config=browser_config, logger=logger)
            start_tasks.append(manager.start())
            managers.append(manager)

        await asyncio.gather(*start_tasks)

        # Distribute URLs among managers
        urls_per_manager = {}
        for i, manager in enumerate(managers):
            start_idx = i * pages_per_browser
            end_idx = min(start_idx + pages_per_browser, len(urls))
            urls_per_manager[manager] = urls[start_idx:end_idx]

        # Approach 1: Create a page for each URL on-demand and run in parallel
        logger.info("Testing approach 1: get_page for each URL + gather", tag="TEST")
        start_time = time.time()

        async def fetch_title_approach1(manager, url):
            """Create a new page for the URL, go to the URL, and get title"""
            crawler_config = CrawlerRunConfig(url=url)
            page, context = await manager.get_page(crawler_config)
            try:
                await page.goto(url)
                title = await page.title()
                return title
            finally:
                await page.close()

        # Run fetch_title_approach1 for each URL in parallel
        tasks = []
        for manager, manager_urls in urls_per_manager.items():
            for url in manager_urls:
                tasks.append(fetch_title_approach1(manager, url))

        approach1_results = await asyncio.gather(*tasks)

        approach1_time = time.time() - start_time
        logger.info(f"Approach 1 time (get_page + gather): {approach1_time:.2f}s", tag="TEST")

        # Approach 2: Get all pages upfront with get_pages, then use them in parallel
        logger.info("Testing approach 2: get_pages upfront + gather", tag="TEST")
        start_time = time.time()

        # Get all pages upfront for each manager
        all_pages = []
        for manager, manager_urls in urls_per_manager.items():
            crawler_config = CrawlerRunConfig()
            pages = await manager.get_pages(crawler_config, count=len(manager_urls))
            all_pages.extend(zip(pages, manager_urls))

        async def fetch_title_approach2(page_ctx, url):
            """Use a pre-created page to go to URL and get title"""
            page, _ = page_ctx
            try:
                await page.goto(url)
                title = await page.title()
                return title
            finally:
                await page.close()

        # Use the pre-created pages to fetch titles in parallel
        tasks = [fetch_title_approach2(page_ctx, url) for page_ctx, url in all_pages]
        approach2_results = await asyncio.gather(*tasks)

        approach2_time = time.time() - start_time
        logger.info(f"Approach 2 time (get_pages + gather): {approach2_time:.2f}s", tag="TEST")

        # Compare results and performance
        speedup = approach1_time / approach2_time if approach2_time > 0 else 0
        pages_per_second = total_pages / approach2_time

        # Show a simple summary
        logger.info(f"📊 Summary: {num_browsers} browsers × {pages_per_browser} pages = {total_pages} total crawls", tag="TEST")
        logger.info(f"⚡ Performance: {pages_per_second:.1f} pages/second ({pages_per_second*60:.0f} pages/minute)", tag="TEST")
        logger.info(f"🚀 Total crawl time: {approach2_time:.2f} seconds", tag="TEST")

        if speedup > 1:
            logger.success(f"✅ Approach 2 (get_pages upfront) was {speedup:.2f}x faster", tag="TEST")
        else:
            logger.info(f"✅ Approach 1 (get_page + gather) was {1/speedup:.2f}x faster", tag="TEST")

        # Close all managers
        for manager in managers:
            await manager.close()

        return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Clean up
        for manager in managers:
            try:
                await manager.close()
            except:
                pass
        return False