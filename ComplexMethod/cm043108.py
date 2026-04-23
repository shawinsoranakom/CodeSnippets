async def demo_proxy_rotation_batch():
    """
    Proxy Rotation Demo with Batch Processing
    =======================================
    Demonstrates proxy rotation using arun_many with memory dispatcher.
    """
    print("\n=== Proxy Rotation Batch Demo ===")

    try:
        # Load proxies and create rotation strategy
        proxies = load_proxies_from_env()
        if not proxies:
            print("No proxies found in environment. Set PROXIES env variable!")
            return

        proxy_strategy = RoundRobinProxyStrategy(proxies)

        # Configurations
        browser_config = BrowserConfig(headless=True, verbose=False)
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            proxy_rotation_strategy=proxy_strategy,
            markdown_generator=DefaultMarkdownGenerator()
        )

        # Test URLs - multiple requests to test rotation
        urls = ["https://httpbin.org/ip"] * (len(proxies) * 2)  # Test each proxy twice

        print("\n📈 Initializing crawler with proxy rotation...")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            monitor = CrawlerMonitor(
                max_visible_rows=10,
                display_mode=DisplayMode.DETAILED
            )

            dispatcher = MemoryAdaptiveDispatcher(
                memory_threshold_percent=80.0,
                check_interval=0.5,
                max_session_permit=1, #len(proxies),  # Match concurrent sessions to proxy count
                # monitor=monitor
            )

            print("\n🚀 Starting batch crawl with proxy rotation...")
            results = await crawler.arun_many(
                urls=urls,
                config=run_config,
                dispatcher=dispatcher
            )

            # Verify results
            success_count = 0
            for result in results:
                if result.success:
                    ip_match = re.search(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}', result.html)
                    current_proxy = run_config.proxy_config if run_config.proxy_config else None

                    if current_proxy and ip_match:
                        print(f"URL {result.url}")
                        print(f"Proxy {current_proxy['server']} -> Response IP: {ip_match.group(0)}")
                        verified = ip_match.group(0) == current_proxy['ip']
                        if verified:
                            print(f"✅ Proxy working! IP matches: {current_proxy['ip']}")
                            success_count += 1
                        else:
                            print("❌ Proxy failed or IP mismatch!")
                    print("---")

            print(f"\n✅ Completed {len(results)} requests with {success_count} successful proxy verifications")

    except Exception as e:
        print(f"\n❌ Error in proxy rotation batch demo: {str(e)}")