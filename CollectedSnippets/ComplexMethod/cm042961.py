async def test_cdp_with_user_data_dir():
    """Test CDP browser with a user data directory and storage state."""
    logger.info("Testing CDP browser with user data directory", tag="TEST")

    # Create a temporary user data directory
    import tempfile
    user_data_dir = tempfile.mkdtemp(prefix="crawl4ai-test-")
    storage_state_file = os.path.join(user_data_dir, "storage_state.json")
    logger.info(f"Created temporary user data directory: {user_data_dir}", tag="TEST")

    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        user_data_dir=user_data_dir
    )

    manager = BrowserManager(browser_config=browser_config, logger=logger)

    try:
        await manager.start()
        logger.info("Browser launched with user data directory", tag="TEST")

        # Navigate to a page and store some data
        crawler_config = CrawlerRunConfig()
        page, context = await manager.get_page(crawler_config)

        # Visit the site first
        await page.goto("https://example.com", wait_until="domcontentloaded")

        # Set a cookie via JavaScript (more reliable for persistence)
        await page.evaluate("""
            document.cookie = 'test_cookie=test_value; path=/; max-age=86400';
        """)

        # Also set via context API for double coverage
        await context.add_cookies([{
            "name": "test_cookie_api",
            "value": "test_value_api",
            "domain": "example.com",
            "path": "/"
        }])

        # Verify cookies were set
        cookies = await context.cookies(["https://example.com"])
        has_test_cookie = any(cookie["name"] in ["test_cookie", "test_cookie_api"] for cookie in cookies)
        logger.info(f"Cookie set successfully: {has_test_cookie}", tag="TEST")

        # Save storage state before closing
        await context.storage_state(path=storage_state_file)
        logger.info(f"Storage state saved to: {storage_state_file}", tag="TEST")

        # Close the browser
        await manager.close()
        logger.info("First browser session closed", tag="TEST")

        # Wait a moment for clean shutdown
        await asyncio.sleep(1.0)

        # Start a new browser with the same user data directory and storage state
        logger.info("Starting second browser session with same user data directory", tag="TEST")
        browser_config2 = BrowserConfig(
            headless=True,
            use_managed_browser=True,
            user_data_dir=user_data_dir,
            storage_state=storage_state_file
        )

        manager2 = BrowserManager(browser_config=browser_config2, logger=logger)
        await manager2.start()

        # Get a new page and check if the cookie persists
        page2, context2 = await manager2.get_page(crawler_config)
        await page2.goto("https://example.com", wait_until="domcontentloaded")

        # Verify cookie persisted
        cookies2 = await context2.cookies(["https://example.com"])
        has_test_cookie2 = any(cookie["name"] in ["test_cookie", "test_cookie_api"] for cookie in cookies2)
        logger.info(f"Cookie persisted across sessions: {has_test_cookie2}", tag="TEST")
        logger.info(f"Cookies found: {[c['name'] for c in cookies2]}", tag="TEST")

        # Clean up
        await manager2.close()

        # Remove temporary directory
        import shutil
        shutil.rmtree(user_data_dir, ignore_errors=True)
        logger.info(f"Removed temporary user data directory", tag="TEST")

        return has_test_cookie and has_test_cookie2
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        try:
            await manager.close()
        except:
            pass
        try:
            await manager2.close()
        except:
            pass

        # Clean up temporary directory
        try:
            import shutil
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except:
            pass

        return False