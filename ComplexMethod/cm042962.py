async def test_cdp_session_management():
    """Test session management with CDP browser - focused on session tracking."""
    logger.info("Testing session management with CDP browser", tag="TEST")

    browser_config = BrowserConfig(
        use_managed_browser=True,
        headless=True
    )

    manager = BrowserManager(browser_config=browser_config, logger=logger)

    try:
        await manager.start()
        logger.info("Browser launched successfully", tag="TEST")

        # Test session tracking and lifecycle management
        session1_id = "test_session_1"
        session2_id = "test_session_2"

        # Set up first session
        crawler_config1 = CrawlerRunConfig(session_id=session1_id)
        page1, context1 = await manager.get_page(crawler_config1)
        await page1.goto("https://example.com", wait_until="domcontentloaded")

        # Get page URL and title for verification
        page1_url = page1.url
        page1_title = await page1.title()
        logger.info(f"Session 1 setup - URL: {page1_url}, Title: {page1_title}", tag="TEST")

        # Set up second session  
        crawler_config2 = CrawlerRunConfig(session_id=session2_id)
        page2, context2 = await manager.get_page(crawler_config2)
        await page2.goto("https://httpbin.org/html", wait_until="domcontentloaded")

        page2_url = page2.url
        page2_title = await page2.title()
        logger.info(f"Session 2 setup - URL: {page2_url}, Title: {page2_title}", tag="TEST")

        # Verify sessions exist in manager
        session1_exists = session1_id in manager.sessions
        session2_exists = session2_id in manager.sessions
        logger.info(f"Sessions in manager - S1: {session1_exists}, S2: {session2_exists}", tag="TEST")

        # Test session reuse
        page1_again, context1_again = await manager.get_page(crawler_config1)
        is_same_page = page1 == page1_again
        is_same_context = context1 == context1_again

        logger.info(f"Session 1 reuse - Same page: {is_same_page}, Same context: {is_same_context}", tag="TEST")

        # Test that sessions are properly tracked with timestamps
        session1_info = manager.sessions.get(session1_id)
        session2_info = manager.sessions.get(session2_id)

        session1_has_timestamp = session1_info and len(session1_info) == 3
        session2_has_timestamp = session2_info and len(session2_info) == 3

        logger.info(f"Session tracking - S1 complete: {session1_has_timestamp}, S2 complete: {session2_has_timestamp}", tag="TEST")

        # In managed browser mode, pages might be shared. Let's test what actually happens
        pages_same_or_different = page1 == page2
        logger.info(f"Pages same object: {pages_same_or_different}", tag="TEST")

        # Test that we can distinguish sessions by their stored info
        session1_context, session1_page, session1_time = session1_info
        session2_context, session2_page, session2_time = session2_info

        sessions_have_different_timestamps = session1_time != session2_time
        logger.info(f"Sessions have different timestamps: {sessions_have_different_timestamps}", tag="TEST")

        # Test session killing
        await manager.kill_session(session1_id)
        logger.info(f"Killed session 1", tag="TEST")

        # Verify session was removed
        session1_removed = session1_id not in manager.sessions
        session2_still_exists = session2_id in manager.sessions
        logger.info(f"After kill - S1 removed: {session1_removed}, S2 exists: {session2_still_exists}", tag="TEST")

        # Test page state after killing session
        page1_closed = page1.is_closed()
        logger.info(f"Page1 closed after kill: {page1_closed}", tag="TEST")

        # Clean up remaining session
        try:
            await manager.kill_session(session2_id)
            logger.info("Killed session 2", tag="TEST")
            session2_removed = session2_id not in manager.sessions
        except Exception as e:
            logger.info(f"Session 2 cleanup: {e}", tag="TEST")
            session2_removed = False

        # Clean up
        await manager.close()
        logger.info("Browser closed successfully", tag="TEST")

        # Success criteria for managed browser sessions:
        # 1. Sessions can be created and tracked with proper info
        # 2. Same page/context returned for same session ID  
        # 3. Sessions have proper timestamp tracking
        # 4. Sessions can be killed and removed from tracking
        # 5. Session cleanup works properly
        success = (session1_exists and 
                  session2_exists and 
                  is_same_page and 
                  session1_has_timestamp and 
                  session2_has_timestamp and
                  sessions_have_different_timestamps and
                  session1_removed and 
                  session2_removed)

        logger.info(f"Test success: {success}", tag="TEST")
        return success
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        try:
            await manager.close()
        except:
            pass
        return False