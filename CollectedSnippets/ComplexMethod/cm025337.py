async def get_coap_context(hass: HomeAssistant) -> COAP:
    """Get CoAP context to be used in all Shelly Gen1 devices."""
    context = COAP()

    adapters = await network.async_get_adapters(hass)
    LOGGER.debug("Network adapters: %s", adapters)

    ipv4: list[IPv4Address] = []
    if not network.async_only_default_interface_enabled(adapters):
        ipv4.extend(
            cast(IPv4Address, address)
            for address in await network.async_get_enabled_source_ips(hass)
            if address.version == 4
            and not (
                address.is_link_local
                or address.is_loopback
                or address.is_multicast
                or address.is_unspecified
            )
        )
    LOGGER.debug("Network IPv4 addresses: %s", ipv4)
    port = get_coiot_port(hass)
    LOGGER.info("Starting CoAP context with UDP port %s", port)
    await context.initialize(port, ipv4)

    @callback
    def shutdown_listener(ev: Event) -> None:
        context.close()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, shutdown_listener)
    return context