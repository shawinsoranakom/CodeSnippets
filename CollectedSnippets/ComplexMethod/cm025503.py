async def async_load_adapters() -> list[Adapter]:
    """Load adapters."""
    source_ip = async_get_source_ip(MDNS_TARGET_IP)
    source_ip_address = ip_address(source_ip) if source_ip else None

    ha_adapters: list[Adapter] = [
        _ifaddr_adapter_to_ha(adapter, source_ip_address)
        for adapter in ifaddr.get_adapters()
    ]

    if not any(adapter["default"] and adapter["auto"] for adapter in ha_adapters):
        for adapter in ha_adapters:
            if _adapter_has_external_address(adapter):
                adapter["auto"] = True

    return ha_adapters