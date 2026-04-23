def _ipv6_address_from_str(ip_str, max_length=MAX_IPV6_ADDRESS_LENGTH):
    if len(ip_str) > max_length:
        raise ValueError(
            f"Unable to convert {ip_str} to an IPv6 address (value too long)."
        )
    return ipaddress.IPv6Address(int(ipaddress.IPv6Address(ip_str)))