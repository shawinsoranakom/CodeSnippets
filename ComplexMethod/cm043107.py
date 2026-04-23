async def demo_proxy_rotation():
    """
    Proxy Rotation Demo using RoundRobinProxyStrategy
    ===============================================
    Demonstrates proxy rotation using the strategy pattern.
    """
    print("\n=== Proxy Rotation Demo (Round Robin) ===")

    # Load proxies and create rotation strategy
    proxies = load_proxies_from_env()
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

    # Test URLs
    urls = ["https://httpbin.org/ip"] * len(proxies)  # Test each proxy once

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in urls:
            result = await crawler.arun(url=url, config=run_config)

            if result.success:
                # Extract IP from response
                ip_match = re.search(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}', result.html)
                current_proxy = run_config.proxy_config if run_config.proxy_config else None

                if current_proxy:
                    print(f"Proxy {current_proxy['server']} -> Response IP: {ip_match.group(0) if ip_match else 'Not found'}")
                    verified = ip_match and ip_match.group(0) == current_proxy['ip']
                    if verified:
                        print(f"✅ Proxy working! IP matches: {current_proxy['ip']}")
                    else:
                        print("❌ Proxy failed or IP mismatch!")
            else:
                print(f"Request failed: {result.error_message}")