async def test_pre_created_context_usage():
    """
    Test that Crawl4AI uses a pre-created browser context instead of creating a new one.

    This simulates the cloud browser service flow:
    1. Start browser with CDP
    2. Create context via raw CDP (simulating cloud service)
    3. Have Crawl4AI connect with browser_context_id
    4. Verify it uses existing context
    """
    logger.info("Testing pre-created context usage", tag="TEST")

    # Start a managed browser first
    browser_config_initial = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        debugging_port=9226,  # Use unique port
        verbose=True
    )

    managed_browser = ManagedBrowser(browser_config=browser_config_initial, logger=logger)
    cdp_creator = None
    manager = None
    context_info = None

    try:
        # Start the browser
        cdp_url = await managed_browser.start()
        logger.info(f"Browser started at {cdp_url}", tag="TEST")

        # Create a context via raw CDP (simulating cloud service)
        cdp_creator = CDPContextCreator(cdp_url)
        context_info = await cdp_creator.create_context()

        logger.info(f"Pre-created context: {context_info['browser_context_id']}", tag="TEST")
        logger.info(f"Pre-created target: {context_info['target_id']}", tag="TEST")

        # Get initial target count
        targets_before = await cdp_creator.get_targets()
        initial_target_count = len(targets_before)
        logger.info(f"Initial target count: {initial_target_count}", tag="TEST")

        # Now create BrowserManager with browser_context_id and target_id
        browser_config = BrowserConfig(
            cdp_url=cdp_url,
            browser_context_id=context_info['browser_context_id'],
            target_id=context_info['target_id'],
            headless=True,
            verbose=True
        )

        manager = BrowserManager(browser_config=browser_config, logger=logger)
        await manager.start()

        logger.info("BrowserManager started with pre-created context", tag="TEST")

        # Get a page
        crawler_config = CrawlerRunConfig()
        page, context = await manager.get_page(crawler_config)

        # Navigate to a test page
        await page.goto("https://example.com", wait_until="domcontentloaded")
        title = await page.title()

        logger.info(f"Page title: {title}", tag="TEST")

        # Get target count after
        targets_after = await cdp_creator.get_targets()
        final_target_count = len(targets_after)
        logger.info(f"Final target count: {final_target_count}", tag="TEST")

        # Verify: target count should not have increased significantly
        # (allow for 1 extra target for internal use, but not many more)
        target_diff = final_target_count - initial_target_count
        logger.info(f"Target count difference: {target_diff}", tag="TEST")

        # Success criteria:
        # 1. Page navigation worked
        # 2. Target count didn't explode (reused existing context)
        success = title == "Example Domain" and target_diff <= 1

        if success:
            logger.success("Pre-created context usage test passed", tag="TEST")
        else:
            logger.error(f"Test failed - Title: {title}, Target diff: {target_diff}", tag="TEST")

        return success

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if manager:
            try:
                await manager.close()
            except:
                pass

        if cdp_creator and context_info:
            try:
                await cdp_creator.dispose_context(context_info['browser_context_id'])
                await cdp_creator.disconnect()
            except:
                pass

        if managed_browser:
            try:
                await managed_browser.cleanup()
            except:
                pass