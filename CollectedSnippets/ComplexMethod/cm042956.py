async def test_context_isolation():
    """
    Test that using browser_context_id actually provides isolation.
    Create two contexts and verify they don't share state.
    """
    logger.info("Testing context isolation with browser_context_id", tag="TEST")

    browser_config_initial = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        debugging_port=9227,
        verbose=True
    )

    managed_browser = ManagedBrowser(browser_config=browser_config_initial, logger=logger)
    cdp_creator = None
    manager1 = None
    manager2 = None
    context_info_1 = None
    context_info_2 = None

    try:
        # Start the browser
        cdp_url = await managed_browser.start()
        logger.info(f"Browser started at {cdp_url}", tag="TEST")

        # Create two separate contexts
        cdp_creator = CDPContextCreator(cdp_url)
        context_info_1 = await cdp_creator.create_context()
        logger.info(f"Context 1: {context_info_1['browser_context_id']}", tag="TEST")

        # Need to reconnect for second context (or use same connection)
        await cdp_creator.disconnect()
        cdp_creator2 = CDPContextCreator(cdp_url)
        context_info_2 = await cdp_creator2.create_context()
        logger.info(f"Context 2: {context_info_2['browser_context_id']}", tag="TEST")

        # Verify contexts are different
        assert context_info_1['browser_context_id'] != context_info_2['browser_context_id'], \
            "Contexts should have different IDs"

        # Connect with first context
        browser_config_1 = BrowserConfig(
            cdp_url=cdp_url,
            browser_context_id=context_info_1['browser_context_id'],
            target_id=context_info_1['target_id'],
            headless=True
        )

        manager1 = BrowserManager(browser_config=browser_config_1, logger=logger)
        await manager1.start()

        # Set a cookie in context 1
        page1, ctx1 = await manager1.get_page(CrawlerRunConfig())
        await page1.goto("https://example.com", wait_until="domcontentloaded")
        await ctx1.add_cookies([{
            "name": "test_isolation",
            "value": "context_1_value",
            "domain": "example.com",
            "path": "/"
        }])

        cookies1 = await ctx1.cookies(["https://example.com"])
        cookie1_value = next((c["value"] for c in cookies1 if c["name"] == "test_isolation"), None)
        logger.info(f"Cookie in context 1: {cookie1_value}", tag="TEST")

        # Connect with second context
        browser_config_2 = BrowserConfig(
            cdp_url=cdp_url,
            browser_context_id=context_info_2['browser_context_id'],
            target_id=context_info_2['target_id'],
            headless=True
        )

        manager2 = BrowserManager(browser_config=browser_config_2, logger=logger)
        await manager2.start()

        # Check cookies in context 2 - should not have the cookie from context 1
        page2, ctx2 = await manager2.get_page(CrawlerRunConfig())
        await page2.goto("https://example.com", wait_until="domcontentloaded")

        cookies2 = await ctx2.cookies(["https://example.com"])
        cookie2_value = next((c["value"] for c in cookies2 if c["name"] == "test_isolation"), None)
        logger.info(f"Cookie in context 2: {cookie2_value}", tag="TEST")

        # Verify isolation
        isolation_works = cookie1_value == "context_1_value" and cookie2_value is None

        if isolation_works:
            logger.success("Context isolation test passed", tag="TEST")
        else:
            logger.error(f"Isolation failed - Cookie1: {cookie1_value}, Cookie2: {cookie2_value}", tag="TEST")

        return isolation_works

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        for mgr in [manager1, manager2]:
            if mgr:
                try:
                    await mgr.close()
                except:
                    pass

        for ctx_info, creator in [(context_info_1, cdp_creator), (context_info_2, cdp_creator2 if 'cdp_creator2' in dir() else None)]:
            if ctx_info and creator:
                try:
                    await creator.dispose_context(ctx_info['browser_context_id'])
                    await creator.disconnect()
                except:
                    pass

        if managed_browser:
            try:
                await managed_browser.cleanup()
            except:
                pass