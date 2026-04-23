def _ip_in_blocked_networks(
    addr: ipaddress.IPv4Address | ipaddress.IPv6Address,
    policy: SSRFPolicy,
) -> str | None:
    """Return a reason string if *addr* falls in a blocked range, else None."""
    # NOTE: if profiling shows this is a hot path, consider memoising with
    # @functools.lru_cache (key on (addr, id(policy))).
    if isinstance(addr, ipaddress.IPv4Address):
        if policy.block_private_ips:
            for net in _BLOCKED_IPV4_NETWORKS:
                if addr in net:
                    return "private IP range"
        for net in policy.additional_blocked_cidrs:  # type: ignore[assignment]
            if isinstance(net, ipaddress.IPv4Network) and addr in net:
                return "blocked CIDR"
    else:
        if policy.block_private_ips:
            for net in _BLOCKED_IPV6_NETWORKS:  # type: ignore[assignment]
                if addr in net:
                    return "private IP range"
        for net in policy.additional_blocked_cidrs:  # type: ignore[assignment]
            if isinstance(net, ipaddress.IPv6Network) and addr in net:
                return "blocked CIDR"

    # Loopback check — independent of block_private_ips so that
    # block_localhost=True still catches 127.x.x.x / ::1 even when
    # private IPs are allowed.
    if policy.block_localhost:
        if isinstance(addr, ipaddress.IPv4Address) and (
            addr in _LOOPBACK_IPV4 or addr in ipaddress.IPv4Network("0.0.0.0/8")
        ):
            return "localhost address"
        if isinstance(addr, ipaddress.IPv6Address) and addr == _LOOPBACK_IPV6:
            return "localhost address"

    # Cloud metadata check — IP set *and* network ranges (e.g. 169.254.0.0/16).
    # Independent of block_private_ips so that allow_private=True still blocks
    # cloud metadata endpoints.
    if policy.block_cloud_metadata:
        if str(addr) in _CLOUD_METADATA_IPS:
            return "cloud metadata endpoint"
        for net in _CLOUD_METADATA_NETWORKS:  # type: ignore[assignment]
            if addr in net:
                return "cloud metadata endpoint"

    return None