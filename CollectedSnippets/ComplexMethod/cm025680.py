def _async_get_zc_args(hass: HomeAssistant) -> dict[str, Any]:
    """Get zeroconf arguments from config."""
    zc_args: dict[str, Any] = {"ip_version": IPVersion.V4Only}
    adapters = network.async_get_loaded_adapters(hass)
    ipv6 = False
    if _async_zc_has_functional_dual_stack():
        if any(adapter["enabled"] and adapter["ipv6"] for adapter in adapters):
            ipv6 = True
            zc_args["ip_version"] = IPVersion.All
    elif not any(adapter["enabled"] and adapter["ipv4"] for adapter in adapters):
        zc_args["ip_version"] = IPVersion.V6Only
        ipv6 = True

    if not ipv6 and network.async_only_default_interface_enabled(adapters):
        zc_args["interfaces"] = InterfaceChoice.Default
    else:
        zc_args["interfaces"] = [
            str(source_ip)
            for source_ip in network.async_get_enabled_source_ips_from_adapters(
                adapters
            )
            if not source_ip.is_loopback
            and not (isinstance(source_ip, IPv6Address) and source_ip.is_global)
            and not (
                isinstance(source_ip, IPv6Address)
                and zc_args["ip_version"] == IPVersion.V4Only
            )
            and not (
                isinstance(source_ip, IPv4Address)
                and zc_args["ip_version"] == IPVersion.V6Only
            )
        ]
    return zc_args