async def test_registry_cleanup(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    config_entry: MockConfigEntry,
    owproxy: MagicMock,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test being able to remove a disconnected device."""
    assert await async_setup_component(hass, "config", {})

    entry_id = config_entry.entry_id
    live_id = "10.111111111111"
    dead_id = "28.111111111111"

    # Initialise with two components
    setup_owproxy_mock_devices(owproxy, [live_id, dead_id])
    await hass.config_entries.async_setup(entry_id)
    await hass.async_block_till_done()

    # Reload with a device no longer on bus
    setup_owproxy_mock_devices(owproxy, [live_id])
    await hass.config_entries.async_reload(entry_id)
    await hass.async_block_till_done()
    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 2

    # Try to remove "10.111111111111" - fails as it is live
    device = device_registry.async_get_device(identifiers={(DOMAIN, live_id)})
    client = await hass_ws_client(hass)
    response = await client.remove_device(device.id, entry_id)
    assert not response["success"]
    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 2
    assert device_registry.async_get_device(identifiers={(DOMAIN, live_id)}) is not None

    # Try to remove "28.111111111111" - succeeds as it is dead
    device = device_registry.async_get_device(identifiers={(DOMAIN, dead_id)})
    response = await client.remove_device(device.id, entry_id)
    assert response["success"]
    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 1
    assert device_registry.async_get_device(identifiers={(DOMAIN, dead_id)}) is None