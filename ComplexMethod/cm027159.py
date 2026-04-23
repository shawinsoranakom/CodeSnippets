async def async_discover_devices(
    hass: HomeAssistant, timeout: int
) -> list[DiscoveredBulb]:
    """Discover wiz devices."""
    broadcast_addrs = await network.async_get_ipv4_broadcast_addresses(hass)
    targets = [str(address) for address in broadcast_addrs]
    combined_discoveries: dict[str, DiscoveredBulb] = {}
    for idx, discovered in enumerate(
        await asyncio.gather(
            *[find_wizlights(timeout, address) for address in targets],
            return_exceptions=True,
        )
    ):
        if isinstance(discovered, Exception):
            _LOGGER.debug("Scanning %s failed with error: %s", targets[idx], discovered)
            continue
        if isinstance(discovered, BaseException):
            raise discovered from None
        for device in discovered:
            assert isinstance(device, DiscoveredBulb)
            combined_discoveries[device.ip_address] = device

    return list(combined_discoveries.values())