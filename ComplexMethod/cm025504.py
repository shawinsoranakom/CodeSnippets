async def async_get_source_ip(
    hass: HomeAssistant, target_ip: str | UndefinedType = UNDEFINED
) -> str:
    """Get the source ip for a target ip."""
    adapters = await async_get_adapters(hass)
    all_ipv4s = []
    for adapter in adapters:
        if adapter["enabled"] and (ipv4s := adapter["ipv4"]):
            all_ipv4s.extend([ipv4["address"] for ipv4 in ipv4s])

    if target_ip is UNDEFINED:
        source_ip = (
            util.async_get_source_ip(PUBLIC_TARGET_IP)
            or util.async_get_source_ip(MDNS_TARGET_IP)
            or util.async_get_source_ip(LOOPBACK_TARGET_IP)
        )
    else:
        source_ip = util.async_get_source_ip(target_ip)

    if not all_ipv4s:
        _LOGGER.warning(
            "Because the system does not have any enabled IPv4 addresses, source"
            " address detection may be inaccurate"
        )
        if source_ip is None:
            raise HomeAssistantError(
                "Could not determine source ip because the system does not have any"
                " enabled IPv4 addresses and creating a socket failed"
            )
        return source_ip

    return source_ip if source_ip in all_ipv4s else all_ipv4s[0]