def is_valid_ipv6_address(ip_addr):
    """
    Return whether the `ip_addr` object is a valid IPv6 address.
    """
    if isinstance(ip_addr, ipaddress.IPv6Address):
        return True
    try:
        _ipv6_address_from_str(ip_addr)
    except (TypeError, ValueError):
        return False
    return True