async def test_discover_routers(
    hass: HomeAssistant, mock_async_zeroconf: MagicMock
) -> None:
    """Test discovering thread routers."""
    mock_async_zeroconf.async_add_service_listener = AsyncMock()
    mock_async_zeroconf.async_remove_service_listener = AsyncMock()
    mock_async_zeroconf.async_get_service_info = AsyncMock()

    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    discovered = []
    removed = []

    @callback
    def router_discovered(key: str, data: discovery.ThreadRouterDiscoveryData) -> None:
        """Handle router discovered."""
        discovered.append((key, data))

    @callback
    def router_removed(key: str) -> None:
        """Handle router removed."""
        removed.append(key)

    # Start Thread router discovery
    thread_disovery = discovery.ThreadRouterDiscovery(
        hass, router_discovered, router_removed
    )
    await thread_disovery.async_start()

    mock_async_zeroconf.async_add_service_listener.assert_called_once_with(
        "_meshcop._udp.local.", ANY
    )
    listener: discovery.ThreadRouterDiscovery.ThreadServiceListener = (
        mock_async_zeroconf.async_add_service_listener.mock_calls[0][1][1]
    )

    # Discover a service
    mock_async_zeroconf.async_get_service_info.return_value = AsyncServiceInfo(
        **ROUTER_DISCOVERY_HASS
    )
    listener.add_service(
        None, ROUTER_DISCOVERY_HASS["type_"], ROUTER_DISCOVERY_HASS["name"]
    )
    await hass.async_block_till_done()
    assert len(discovered) == 1
    assert len(removed) == 0
    assert discovered[-1] == (
        "aeeb2f594b570bbf",
        discovery.ThreadRouterDiscoveryData(
            instance_name="HomeAssistant OpenThreadBorderRouter #0BBF",
            addresses=["192.168.0.115"],
            border_agent_id="230c6a1ac57f6f4be262acf32e5ef52c",
            brand="homeassistant",
            extended_address="aeeb2f594b570bbf",
            extended_pan_id="e60fc7c186212ce5",
            model_name="OpenThreadBorderRouter",
            network_name="OpenThread HC",
            server="core-silabs-multiprotocol.local.",
            thread_version="1.3.0",
            unconfigured=None,
            vendor_name="HomeAssistant",
        ),
    )

    # Discover another service - we don't care if zeroconf considers this an update
    mock_async_zeroconf.async_get_service_info.return_value = AsyncServiceInfo(
        **ROUTER_DISCOVERY_GOOGLE_1
    )
    listener.update_service(
        None, ROUTER_DISCOVERY_GOOGLE_1["type_"], ROUTER_DISCOVERY_GOOGLE_1["name"]
    )
    await hass.async_block_till_done()
    assert len(discovered) == 2
    assert len(removed) == 0
    assert discovered[-1] == (
        "f6a99b425a67abed",
        discovery.ThreadRouterDiscoveryData(
            instance_name="Google-Nest-Hub-#ABED",
            addresses=["192.168.0.124"],
            border_agent_id="bc3740c3e963aa8735bebecd7cc503c7",
            brand="google",
            extended_address="f6a99b425a67abed",
            extended_pan_id="9e75e256f61409a3",
            model_name="Google Nest Hub",
            network_name="NEST-PAN-E1AF",
            server="2d99f293-cd8e-2770-8dd2-6675de9fa000.local.",
            thread_version="1.3.0",
            unconfigured=None,
            vendor_name="Google Inc.",
        ),
    )

    # Remove a service
    listener.remove_service(
        None, ROUTER_DISCOVERY_HASS["type_"], ROUTER_DISCOVERY_HASS["name"]
    )
    await hass.async_block_till_done()
    assert len(discovered) == 2
    assert len(removed) == 1
    assert removed[-1] == "aeeb2f594b570bbf"

    # Remove the service again
    listener.remove_service(
        None, ROUTER_DISCOVERY_HASS["type_"], ROUTER_DISCOVERY_HASS["name"]
    )
    await hass.async_block_till_done()
    assert len(discovered) == 2
    assert len(removed) == 1

    # Remove an unknown service
    listener.remove_service(None, ROUTER_DISCOVERY_HASS["type_"], "unknown")
    await hass.async_block_till_done()
    assert len(discovered) == 2
    assert len(removed) == 1

    # Stop Thread router discovery
    await thread_disovery.async_stop()
    mock_async_zeroconf.async_remove_service_listener.assert_called_once_with(listener)