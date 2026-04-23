async def test_browser_mode(adapter_name: str, adapter=None):
    """Test a browser mode and return results"""
    print(f"\n{'='*60}")
    print(f"Testing: {adapter_name}")
    print(f"{'='*60}")

    browser_config = BrowserConfig(
        headless=False,  # Run in headed mode for better results
        verbose=True,
        viewport_width=1920,
        viewport_height=1080,
    )

    if adapter:
        # Use undetected mode
        crawler_strategy = AsyncPlaywrightCrawlerStrategy(
            browser_config=browser_config,
            browser_adapter=adapter
        )
        crawler = AsyncWebCrawler(
            crawler_strategy=crawler_strategy,
            config=browser_config
        )
    else:
        # Use regular mode
        crawler = AsyncWebCrawler(config=browser_config)

    async with crawler:
        config = CrawlerRunConfig(
            delay_before_return_html=3.0,  # Let detection scripts run
            wait_for_images=True,
            screenshot=True,
            simulate_user=False,  # Don't simulate for accurate detection
        )

        result = await crawler.arun(url=TEST_URL, config=config)

        print(f"\n✓ Success: {result.success}")
        print(f"✓ Status Code: {result.status_code}")

        if result.success:
            # Analyze detection results
            detections = analyze_bot_detection(result)

            print(f"\n🔍 Bot Detection Analysis:")
            print(f"  - WebDriver Detected: {'❌ Yes' if detections['webdriver'] else '✅ No'}")
            print(f"  - Headless Detected: {'❌ Yes' if detections['headless'] else '✅ No'}")
            print(f"  - Automation Detected: {'❌ Yes' if detections['automation'] else '✅ No'}")
            print(f"  - Failed Tests: {detections['failed_tests']}")

            # Show some content
            if result.markdown.raw_markdown:
                print(f"\nContent preview:")
                lines = result.markdown.raw_markdown.split('\n')
                for line in lines[:20]:  # Show first 20 lines
                    if any(keyword in line.lower() for keyword in ['test', 'pass', 'fail', 'yes', 'no']):
                        print(f"  {line.strip()}")

        return result, detections if result.success else {}