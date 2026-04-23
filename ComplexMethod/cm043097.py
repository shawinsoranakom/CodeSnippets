async def proxy_rotation():
    """
    PART 4: Proxy Rotation

    This function demonstrates:
    - Setting up a proxy rotation strategy
    - Using multiple proxies in a round-robin fashion
    """
    print("\n===== PROXY ROTATION =====")
    print("This example shows how to implement proxy rotation for distributed crawling.")

    # Load proxies and create rotation strategy
    proxies = ProxyConfig.from_env()
    #eg: export PROXIES="ip1:port1:username1:password1,ip2:port2:username2:password2"
    if not proxies:
        print("No proxies found in environment. Set PROXIES env variable!")
        return

    proxy_strategy = RoundRobinProxyStrategy(proxies)

    # Create configs
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        proxy_rotation_strategy=proxy_strategy
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        urls = ["https://httpbin.org/ip"] * (len(proxies) * 2)  # Test each proxy twice

        print("\n📈 Initializing crawler with proxy rotation...")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print("\n🚀 Starting batch crawl with proxy rotation...")
            results = await crawler.arun_many(
                urls=urls,
                config=run_config
            )
            for result in results:
                if result.success:
                    ip_match = re.search(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}', result.html)
                    current_proxy = run_config.proxy_config if run_config.proxy_config else None

                    if current_proxy and ip_match:
                        print(f"URL {result.url}")
                        print(f"Proxy {current_proxy.server} -> Response IP: {ip_match.group(0)}")
                        verified = ip_match.group(0) == current_proxy.ip
                        if verified:
                            print(f"✅ Proxy working! IP matches: {current_proxy.ip}")
                        else:
                            print("❌ Proxy failed or IP mismatch!")
                    print("---")
                else:
                    print(f"❌ Crawl via proxy failed!: {result.error_message}")