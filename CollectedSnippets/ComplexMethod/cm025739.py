async def async_discover_devices(
    hass: HomeAssistant, timeout: int, address: str | None = None
) -> list[ElkSystem]:
    """Discover elkm1 devices."""
    if address:
        targets = [address]
    else:
        targets = [
            str(broadcast_address)
            for broadcast_address in await network.async_get_ipv4_broadcast_addresses(
                hass
            )
        ]

    scanner = AIOELKDiscovery()
    combined_discoveries: dict[str, ElkSystem] = {}
    for idx, discovered in enumerate(
        await asyncio.gather(
            *[
                scanner.async_scan(timeout=timeout, address=target_address)
                for target_address in targets
            ],
            return_exceptions=True,
        )
    ):
        if isinstance(discovered, Exception):
            _LOGGER.debug("Scanning %s failed with error: %s", targets[idx], discovered)
            continue
        if isinstance(discovered, BaseException):
            raise discovered from None
        for device in discovered:
            assert isinstance(device, ElkSystem)
            combined_discoveries[device.ip_address] = device

    return list(combined_discoveries.values())