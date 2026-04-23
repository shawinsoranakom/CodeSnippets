async def async_discover_devices(
    hass: HomeAssistant, timeout: int, address: str | None = None
) -> list[FluxLEDDiscovery]:
    """Discover flux led devices."""
    if address:
        targets = [address]
    else:
        targets = [
            str(broadcast_address)
            for broadcast_address in await network.async_get_ipv4_broadcast_addresses(
                hass
            )
        ]

    scanner = AIOBulbScanner()
    for idx, discovered in enumerate(
        await asyncio.gather(
            *[
                create_eager_task(
                    scanner.async_scan(timeout=timeout, address=target_address)
                )
                for target_address in targets
            ],
            return_exceptions=True,
        )
    ):
        if isinstance(discovered, Exception):
            _LOGGER.debug("Scanning %s failed with error: %s", targets[idx], discovered)
            continue

    if not address:
        return scanner.getBulbInfo()

    return [
        device for device in scanner.getBulbInfo() if device[ATTR_IPADDR] == address
    ]