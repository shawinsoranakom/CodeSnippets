async def demo_deep_with_proxy(client: httpx.AsyncClient):
    proxy_params_list = load_proxies_from_env()  # Get the list of parameter dicts
    if not proxy_params_list:
        console.rule(
            "[bold yellow]Demo 6c: Deep Crawl + Proxies (SKIPPED)[/]", style="yellow")
        console.print("Set the PROXIES environment variable to run this demo.")
        return

    payload = {
        # Use a site likely accessible via proxies
        "urls": [DEEP_CRAWL_BASE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "proxy_rotation_strategy": {
                    "type": "RoundRobinProxyStrategy",
                    "params": {
                        # Correctly create the list of {"type": ..., "params": ...} structures, excluding the demo 'ip' key
                        "proxies": [
                            {"type": "ProxyConfig", "params": {
                                k: v for k, v in p.items() if k != 'ip'}}
                            for p in proxy_params_list
                        ]
                    }
                },
                "deep_crawl_strategy": {
                    "type": "BFSDeepCrawlStrategy",
                    "params": {
                        "max_depth": 1,  # Just crawl start URL via proxy
                        "max_pages": 5,
                    }
                }
            }
        }
    }
    # make_request calls print_result_summary, which shows URL and success status
    results = await make_request(client, "/crawl", payload, "Demo 6c: Deep Crawl + Proxies")
    if not results:
        console.print("[red]No results returned from the crawl.[/]")
        return
    console.print("[cyan]Proxy Usage Summary from Deep Crawl:[/]")
    # Verification of specific proxy IP usage would require more complex setup or server logs.
    for result in results:
        if result.get("success") and result.get("metadata"):
            proxy_ip = result["metadata"].get("proxy_ip", "N/A")
            console.print(f"  Proxy IP used: {proxy_ip}")
        elif not result.get("success"):
            console.print(f"  [red]Error: {result['error_message']}[/]")