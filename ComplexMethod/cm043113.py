def load_proxies_from_env() -> List[Dict]:
    """
    Load proxies from the PROXIES environment variable.
    Expected format: IP:PORT:USER:PASS,IP:PORT,IP2:PORT2:USER2:PASS2,...
    Returns a list of dictionaries suitable for the 'params' of ProxyConfig.
    """
    proxies_params_list = []
    proxies_str = os.getenv("PROXIES", "")
    if not proxies_str:
        # console.print("[yellow]PROXIES environment variable not set or empty.[/]")
        return proxies_params_list  # Return empty list if not set

    try:
        proxy_entries = proxies_str.split(",")
        for entry in proxy_entries:
            entry = entry.strip()
            if not entry:
                continue

            parts = entry.split(":")
            proxy_dict = {}

            if len(parts) == 4:  # Format: IP:PORT:USER:PASS
                ip, port, username, password = parts
                proxy_dict = {
                    "server": f"http://{ip}:{port}",  # Assuming http protocol
                    "username": username,
                    "password": password,
                    # "ip": ip # 'ip' is not a standard ProxyConfig param, 'server' contains it
                }
            elif len(parts) == 2:  # Format: IP:PORT
                ip, port = parts
                proxy_dict = {
                    "server": f"http://{ip}:{port}",
                    # "ip": ip
                }
            else:
                console.print(
                    f"[yellow]Skipping invalid proxy string format:[/yellow] {entry}")
                continue

            proxies_params_list.append(proxy_dict)

    except Exception as e:
        console.print(
            f"[red]Error loading proxies from environment:[/red] {e}")

    if proxies_params_list:
        console.print(
            f"[cyan]Loaded {len(proxies_params_list)} proxies from environment.[/]")
    # else:
    #     console.print("[yellow]No valid proxies loaded from environment.[/]")

    return proxies_params_list