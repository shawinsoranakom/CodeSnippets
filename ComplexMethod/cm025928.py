def _normalize_ips_and_network(hosts: list[str]) -> list[str] | None:
    """Check if a list of hosts are all ips or ip networks."""
    normalized_hosts = []

    for host in sorted(hosts):
        try:
            start, end = host.split("-", 1)
            if "." not in end:
                ip_1, ip_2, ip_3, _ = start.split(".", 3)
                end = f"{ip_1}.{ip_2}.{ip_3}.{end}"
            summarize_address_range(ip_address(start), ip_address(end))
        except ValueError:
            pass
        else:
            normalized_hosts.append(host)
            continue

        try:
            normalized_hosts.append(str(ip_address(host)))
        except ValueError:
            pass
        else:
            continue

        try:
            normalized_hosts.append(str(ip_network(host)))
        except ValueError:
            return None

    return normalized_hosts