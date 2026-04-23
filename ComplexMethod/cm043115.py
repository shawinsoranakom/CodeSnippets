async def demo_param_proxy(client: httpx.AsyncClient):
    proxy_params_list = load_proxies_from_env()  # Get the list of parameter dicts
    if not proxy_params_list:
        console.rule(
            "[bold yellow]Demo 3e: Using Proxies (SKIPPED)[/]", style="yellow")
        console.print("Set the PROXIES environment variable to run this demo.")
        console.print("Format: IP:PORT:USR:PWD,IP:PORT,...")
        return

    payload = {
        "urls": ["https://httpbin.org/ip"],  # URL that shows originating IP
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "proxy_rotation_strategy": {
                    "type": "RoundRobinProxyStrategy",
                    "params": {
                        "proxies": [
                            # [
                            # {
                            # "type": "ProxyConfig",
                            # "params": {
                            # server:"...",
                            # "username": "...",
                            # "password": "..."
                            # }
                            # },
                            # ...
                            # ]

                            # Filter out the 'ip' key when sending to server, as it's not part of ProxyConfig
                            {"type": "ProxyConfig", "params": {
                                k: v for k, v in p.items() if k != 'ip'}}
                            for p in proxy_params_list
                        ]
                    }
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 3e: Using Proxies")

    # --- Verification Logic ---
    if results and results[0].get("success"):
        result = results[0]
        try:
            # httpbin.org/ip returns JSON within the HTML body's <pre> tag
            html_content = result.get('html', '')
            # Basic extraction - find JSON within <pre> tags or just the JSON itself
            json_str = None
            if '<pre' in html_content:
                start = html_content.find('{')
                end = html_content.rfind('}')
                if start != -1 and end != -1:
                    json_str = html_content[start:end+1]
            elif html_content.strip().startswith('{'):  # Maybe it's just JSON
                json_str = html_content.strip()

            if json_str:
                ip_data = json.loads(json_str)
                origin_ip = ip_data.get("origin")
                console.print(
                    f"  Origin IP reported by httpbin: [bold yellow]{origin_ip}[/]")

                # Extract the IPs from the proxy list for comparison
                proxy_ips = {p.get("server").split(
                    ":")[1][2:] for p in proxy_params_list}

                if origin_ip and origin_ip in proxy_ips:
                    console.print(
                        "[bold green]  Verification SUCCESS: Origin IP matches one of the provided proxies![/]")
                elif origin_ip:
                    console.print(
                        "[bold red]  Verification FAILED: Origin IP does not match any provided proxy IPs.[/]")
                    console.print(f"  Provided Proxy IPs: {proxy_ips}")
                else:
                    console.print(
                        "[yellow]  Verification SKIPPED: Could not extract origin IP from response.[/]")
            else:
                console.print(
                    "[yellow]  Verification SKIPPED: Could not find JSON in httpbin response HTML.[/]")
                # console.print(f"HTML Received:\n{html_content[:500]}...") # Uncomment for debugging

        except json.JSONDecodeError:
            console.print(
                "[red]  Verification FAILED: Could not parse JSON from httpbin response HTML.[/]")
        except Exception as e:
            console.print(
                f"[red]  Verification Error: An unexpected error occurred during IP check: {e}[/]")
    elif results:
        console.print(
            "[yellow]  Verification SKIPPED: Crawl for IP check was not successful.[/]")