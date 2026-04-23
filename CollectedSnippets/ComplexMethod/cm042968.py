async def test_parallel_approaches_comparison():
    """Compare two parallel crawling approaches:
    1. Create a page for each URL on-demand (get_page + gather)
    2. Get all pages upfront with get_pages, then use them (get_pages + gather)
    """
    logger.info("Comparing different parallel crawling approaches", tag="TEST")

    urls = [
        "https://example.com/page1",
        "https://crawl4ai.com",
        "https://kidocode.com",
        "https://bbc.com",
        # "https://example.com/page1",
        # "https://example.com/page2",
        # "https://example.com/page3",
        # "https://example.com/page4",
    ]

    browser_config = BrowserConfig(headless=False)
    manager = BrowserManager(browser_config=browser_config, logger=logger)

    try:
        await manager.start()

        # Approach 1: Create a page for each URL on-demand and run in parallel
        logger.info("Testing approach 1: get_page for each URL + gather", tag="TEST")
        start_time = time.time()

        async def fetch_title_approach1(url):
            """Create a new page for each URL, go to the URL, and get title"""
            crawler_config = CrawlerRunConfig(url=url)
            page, context = await manager.get_page(crawler_config)
            try:
                await page.goto(url)
                title = await page.title()
                return title
            finally:
                await page.close()

        # Run fetch_title_approach1 for each URL in parallel
        tasks = [fetch_title_approach1(url) for url in urls]
        approach1_results = await asyncio.gather(*tasks)

        approach1_time = time.time() - start_time
        logger.info(f"Approach 1 time (get_page + gather): {approach1_time:.2f}s", tag="TEST")

        # Approach 2: Get all pages upfront with get_pages, then use them in parallel
        logger.info("Testing approach 2: get_pages upfront + gather", tag="TEST")
        start_time = time.time()

        # Get all pages upfront
        crawler_config = CrawlerRunConfig()
        pages = await manager.get_pages(crawler_config, count=len(urls))

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
        tasks = [fetch_title_approach2(page_ctx, url) for page_ctx, url in zip(pages, urls)]
        approach2_results = await asyncio.gather(*tasks)

        approach2_time = time.time() - start_time
        logger.info(f"Approach 2 time (get_pages + gather): {approach2_time:.2f}s", tag="TEST")

        # Compare results and performance
        speedup = approach1_time / approach2_time if approach2_time > 0 else 0
        if speedup > 1:
            logger.success(f"Approach 2 (get_pages upfront) was {speedup:.2f}x faster", tag="TEST")
        else:
            logger.info(f"Approach 1 (get_page + gather) was {1/speedup:.2f}x faster", tag="TEST")

        # Verify same content was retrieved in both approaches
        assert len(approach1_results) == len(approach2_results), "Result count mismatch"

        # Sort results for comparison since parallel execution might complete in different order
        assert sorted(approach1_results) == sorted(approach2_results), "Results content mismatch"

        await manager.close()
        return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        try:
            await manager.close()
        except:
            pass
        return False