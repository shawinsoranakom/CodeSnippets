def info_from_service(service: AsyncServiceInfo) -> _ZeroconfServiceInfo | None:
    """Return prepared info from mDNS entries."""
    # See https://ietf.org/rfc/rfc6763.html#section-6.4 and
    # https://ietf.org/rfc/rfc6763.html#section-6.5 for expected encodings
    # for property keys and values
    if not (maybe_ip_addresses := service.ip_addresses_by_version(IPVersion.All)):
        return None
    if TYPE_CHECKING:
        ip_addresses = cast(list[IPv4Address | IPv6Address], maybe_ip_addresses)
    else:
        ip_addresses = maybe_ip_addresses
    ip_address: IPv4Address | IPv6Address | None = None
    for ip_addr in ip_addresses:
        if not ip_addr.is_link_local and not ip_addr.is_unspecified:
            ip_address = ip_addr
            break
    if not ip_address:
        return None

    if TYPE_CHECKING:
        assert service.server is not None, (
            "server cannot be none if there are addresses"
        )
    return _ZeroconfServiceInfo(
        ip_address=ip_address,
        ip_addresses=ip_addresses,
        port=service.port,
        hostname=service.server,
        type=service.type,
        name=service.name,
        properties=service.decoded_properties,
    )