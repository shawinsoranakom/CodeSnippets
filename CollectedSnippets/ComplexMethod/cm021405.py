async def test_remove_device_token_needed(
    hass: HomeAssistant,
    mock_bridge,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test being able to remove a disconnected device."""
    assert await async_setup_component(hass, "config", {})
    entry = await init_integration(hass, USERNAME, TOKEN)
    entry_id = entry.entry_id
    assert mock_bridge

    mock_bridge.mock_callbacks([DUMMY_HEATER_DEVICE])
    await hass.async_block_till_done()

    assert mock_bridge.is_running is True
    assert len(entry.runtime_data) == 1

    live_device_id = DUMMY_DEVICE_ID10
    dead_device_id = DUMMY_DEVICE_ID4

    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 1

    # Create a dead device
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, dead_device_id)},
        manufacturer="Switcher",
        model="Switcher Model",
        name="Switcher Device",
    )
    await hass.async_block_till_done()
    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 2

    # Try to remove a live device - fails
    device = device_registry.async_get_device(identifiers={(DOMAIN, live_device_id)})
    client = await hass_ws_client(hass)
    response = await client.remove_device(device.id, entry_id)
    assert not response["success"]
    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 2
    assert (
        device_registry.async_get_device(identifiers={(DOMAIN, live_device_id)})
        is not None
    )

    # Try to remove a dead device - succeeds
    device = device_registry.async_get_device(identifiers={(DOMAIN, dead_device_id)})
    response = await client.remove_device(device.id, entry_id)
    assert response["success"]
    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 1
    assert (
        device_registry.async_get_device(identifiers={(DOMAIN, dead_device_id)}) is None
    )