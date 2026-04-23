async def test_discover_routers(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    mock_async_zeroconf: MagicMock,
) -> None:
    """Test discovering thread routers."""
    mock_async_zeroconf.async_add_service_listener = AsyncMock()
    mock_async_zeroconf.async_remove_service_listener = AsyncMock()
    mock_async_zeroconf.async_get_service_info = AsyncMock()

    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    # Subscribe
    await client.send_json({"id": 1, "type": "thread/discover_routers"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

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
    msg = await client.receive_json()
    assert msg == {
        "event": {
            "data": {
                "instance_name": "HomeAssistant OpenThreadBorderRouter #0BBF",
                "addresses": ["192.168.0.115"],
                "border_agent_id": "230c6a1ac57f6f4be262acf32e5ef52c",
                "brand": "homeassistant",
                "extended_address": "aeeb2f594b570bbf",
                "extended_pan_id": "e60fc7c186212ce5",
                "model_name": "OpenThreadBorderRouter",
                "network_name": "OpenThread HC",
                "server": "core-silabs-multiprotocol.local.",
                "thread_version": "1.3.0",
                "unconfigured": None,
                "vendor_name": "HomeAssistant",
            },
            "key": "aeeb2f594b570bbf",
            "type": "router_discovered",
        },
        "id": 1,
        "type": "event",
    }

    # Discover another service - we don't care if zeroconf considers this an update
    mock_async_zeroconf.async_get_service_info.return_value = AsyncServiceInfo(
        **ROUTER_DISCOVERY_GOOGLE_1
    )
    listener.update_service(
        None, ROUTER_DISCOVERY_GOOGLE_1["type_"], ROUTER_DISCOVERY_GOOGLE_1["name"]
    )
    msg = await client.receive_json()
    assert msg == {
        "event": {
            "data": {
                "addresses": ["192.168.0.124"],
                "border_agent_id": "bc3740c3e963aa8735bebecd7cc503c7",
                "brand": "google",
                "extended_address": "f6a99b425a67abed",
                "extended_pan_id": "9e75e256f61409a3",
                "instance_name": "Google-Nest-Hub-#ABED",
                "model_name": "Google Nest Hub",
                "network_name": "NEST-PAN-E1AF",
                "server": "2d99f293-cd8e-2770-8dd2-6675de9fa000.local.",
                "thread_version": "1.3.0",
                "unconfigured": None,
                "vendor_name": "Google Inc.",
            },
            "key": "f6a99b425a67abed",
            "type": "router_discovered",
        },
        "id": 1,
        "type": "event",
    }

    # Remove a service
    listener.remove_service(
        None, ROUTER_DISCOVERY_HASS["type_"], ROUTER_DISCOVERY_HASS["name"]
    )
    msg = await client.receive_json()
    assert msg == {
        "event": {"key": "aeeb2f594b570bbf", "type": "router_removed"},
        "id": 1,
        "type": "event",
    }

    # Unsubscribe
    await client.send_json({"id": 2, "type": "unsubscribe_events", "subscription": 1})
    response = await client.receive_json()
    assert response["success"]

    mock_async_zeroconf.async_remove_service_listener.assert_called_once_with(listener)