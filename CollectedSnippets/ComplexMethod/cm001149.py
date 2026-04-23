async def _resolve_host(hostname: str) -> list[str]:
    """
    Resolves the hostname to a list of IP addresses (IPv4 first, then IPv6).
    """
    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError(f"Unable to resolve IP address for hostname {hostname}")

    ip_list = [info[4][0] for info in infos]
    ipv4 = [ip for ip in ip_list if ":" not in ip]
    ipv6 = [ip for ip in ip_list if ":" in ip]
    ip_addresses = ipv4 + ipv6

    if not ip_addresses:
        raise ValueError(f"No IP addresses found for {hostname}")
    return ip_addresses