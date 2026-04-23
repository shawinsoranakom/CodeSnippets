def is_host_allowed(hostname: str, ip: str | None = None) -> bool:
    """Check if a hostname or IP is in the allowed hosts list.

    Args:
        hostname: Hostname to check
        ip: Optional IP address to check

    Returns:
        bool: True if hostname or IP is in the allowed list, False otherwise.
    """
    allowed_hosts = get_allowed_hosts()
    if not allowed_hosts:
        return False

    # Check hostname match
    if hostname in allowed_hosts:
        return True

    # Check if hostname matches any wildcard patterns
    for allowed in allowed_hosts:
        if allowed.startswith("*."):
            # Wildcard domain matching
            domain_suffix = allowed[1:]  # Remove the *
            if hostname.endswith(domain_suffix) or hostname == domain_suffix[1:]:
                return True

    # Check IP-based matching if IP is provided
    if ip:
        try:
            ip_obj = ipaddress.ip_address(ip)

            # Check exact IP match
            if ip in allowed_hosts:
                return True

            # Check CIDR range match
            for allowed in allowed_hosts:
                try:
                    # Try to parse as CIDR network
                    if "/" in allowed:
                        network = ipaddress.ip_network(allowed, strict=False)
                        if ip_obj in network:
                            return True
                except (ValueError, ipaddress.AddressValueError):
                    # Not a valid CIDR, skip
                    continue

        except (ValueError, ipaddress.AddressValueError):
            # Invalid IP, skip IP-based checks
            pass

    return False