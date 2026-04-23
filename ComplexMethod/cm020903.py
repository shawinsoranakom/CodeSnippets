async def test_remove_config_entry_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    config_entry_factory: ConfigEntryFactoryType,
    client_payload: list[dict[str, Any]],
    device_payload: list[dict[str, Any]],
    mock_websocket_message: WebsocketMessageMock,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Verify removing a device manually."""
    config_entry = await config_entry_factory()

    assert await async_setup_component(hass, "config", {})
    ws_client = await hass_ws_client(hass)

    # Try to remove an active client from UI: allowed
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, client_payload[0]["mac"])}
    )
    response = await ws_client.remove_device(device_entry.id, config_entry.entry_id)
    assert response["success"]
    assert not device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, client_payload[0]["mac"])}
    )

    # Try to remove an active device from UI: not allowed
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, device_payload[0]["mac"])}
    )
    response = await ws_client.remove_device(device_entry.id, config_entry.entry_id)
    assert not response["success"]
    assert device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, device_payload[0]["mac"])}
    )

    # Remove a client from Unifi API
    mock_websocket_message(message=MessageKey.CLIENT_REMOVED, data=[client_payload[1]])
    await hass.async_block_till_done()

    # Try to remove an inactive client from UI: allowed
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, client_payload[1]["mac"])}
    )
    response = await ws_client.remove_device(device_entry.id, config_entry.entry_id)
    assert response["success"]
    assert not device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, client_payload[1]["mac"])}
    )