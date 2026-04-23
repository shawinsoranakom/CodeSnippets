async def test_network_console_capture():
    print("\n=== Testing Network and Console Capture ===\n")

    # Start test server
    runner = await start_test_server()
    try:
        browser_config = BrowserConfig(headless=True)

        # Test with capture disabled (default)
        print("\n1. Testing with capture disabled (default)...")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                wait_until="networkidle",  # Wait for network to be idle
            )
            result = await crawler.arun(url="http://localhost:8080/", config=config)

            assert result.network_requests is None, "Network requests should be None when capture is disabled"
            assert result.console_messages is None, "Console messages should be None when capture is disabled"
            print("✓ Default config correctly returns None for network_requests and console_messages")

        # Test with network capture enabled
        print("\n2. Testing with network capture enabled...")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                wait_until="networkidle",  # Wait for network to be idle
                capture_network_requests=True
            )
            result = await crawler.arun(url="http://localhost:8080/", config=config)

            assert result.network_requests is not None, "Network requests should be captured"
            print(f"✓ Captured {len(result.network_requests)} network requests")

            # Check if we have both requests and responses
            request_count = len([r for r in result.network_requests if r.get("event_type") == "request"])
            response_count = len([r for r in result.network_requests if r.get("event_type") == "response"])
            print(f"  - {request_count} requests, {response_count} responses")

            # Check if we captured specific resources
            urls = [r.get("url") for r in result.network_requests]
            has_image = any("/image.png" in url for url in urls)
            has_api_data = any("/api/data" in url for url in urls)
            has_api_json = any("/api/json" in url for url in urls)

            assert has_image, "Should have captured image request"
            assert has_api_data, "Should have captured API data request"
            assert has_api_json, "Should have captured API JSON request"
            print("✓ Captured expected network requests (image, API endpoints)")

        # Test with console capture enabled
        print("\n3. Testing with console capture enabled...")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                wait_until="networkidle",  # Wait for network to be idle
                capture_console_messages=True
            )
            result = await crawler.arun(url="http://localhost:8080/", config=config)

            assert result.console_messages is not None, "Console messages should be captured"
            print(f"✓ Captured {len(result.console_messages)} console messages")

            # Check if we have different types of console messages
            message_types = set(msg.get("type") for msg in result.console_messages if "type" in msg)
            print(f"  - Message types: {', '.join(message_types)}")

            # Print all captured messages for debugging
            print("  - Captured messages:")
            for msg in result.console_messages:
                print(f"    * Type: {msg.get('type', 'N/A')}, Text: {msg.get('text', 'N/A')}")

            # Look for specific messages
            messages = [msg.get("text") for msg in result.console_messages if "text" in msg]
            has_basic_log = any("Basic console log" in msg for msg in messages)
            has_error_msg = any("Error message" in msg for msg in messages)
            has_warning_msg = any("Warning message" in msg for msg in messages)

            assert has_basic_log, "Should have captured basic console.log message"
            assert has_error_msg, "Should have captured console.error message"
            assert has_warning_msg, "Should have captured console.warn message"
            print("✓ Captured expected console messages (log, error, warning)")

        # Test with both captures enabled
        print("\n4. Testing with both network and console capture enabled...")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                wait_until="networkidle",  # Wait for network to be idle
                capture_network_requests=True,
                capture_console_messages=True
            )
            result = await crawler.arun(url="http://localhost:8080/", config=config)

            assert result.network_requests is not None, "Network requests should be captured"
            assert result.console_messages is not None, "Console messages should be captured"
            print(f"✓ Successfully captured both {len(result.network_requests)} network requests and {len(result.console_messages)} console messages")

    finally:
        await runner.cleanup()
        print("\nTest server shutdown")