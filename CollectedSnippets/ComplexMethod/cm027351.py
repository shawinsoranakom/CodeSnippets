async def async_discover_devices(
    hass: HomeAssistant, timeout: int, address: str | None = None
) -> list[Device30303]:
    """Discover devices."""
    if address:
        targets = [address]
    else:
        targets = [
            str(broadcast_address)
            for broadcast_address in await network.async_get_ipv4_broadcast_addresses(
                hass
            )
        ]

    scanner = AIODiscovery30303()
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

    _LOGGER.debug("Found devices: %s", scanner.found_devices)
    if not address:
        return [
            device
            for device in scanner.found_devices
            if async_is_steamist_device(device)
        ]

    return [device for device in scanner.found_devices if device.ipaddress == address]