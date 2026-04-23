async def test_registry_cleanup(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    config_entry: ConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test being able to remove a disconnected device."""
    assert await async_setup_component(hass, "config", {})
    entry_id = config_entry.entry_id
    live_id = "VF1ZOE40VIN"
    dead_id = "VF1AAAAA555777888"

    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 0
    device_registry.async_get_or_create(
        config_entry_id=entry_id,
        identifiers={(DOMAIN, dead_id)},
        manufacturer="Renault",
        model="Zoe",
        name="REGISTRATION-NUMBER",
        sw_version="X101VE",
    )
    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 1

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 2

    # Try to remove "VF1ZOE40VIN" - fails as it is live
    device = device_registry.async_get_device(identifiers={(DOMAIN, live_id)})
    client = await hass_ws_client(hass)
    response = await client.remove_device(device.id, entry_id)
    assert not response["success"]
    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 2
    assert device_registry.async_get_device(identifiers={(DOMAIN, live_id)}) is not None

    # Try to remove "VF1AAAAA555777888" - succeeds as it is dead
    device = device_registry.async_get_device(identifiers={(DOMAIN, dead_id)})
    response = await client.remove_device(device.id, entry_id)
    assert response["success"]
    assert len(dr.async_entries_for_config_entry(device_registry, entry_id)) == 1
    assert device_registry.async_get_device(identifiers={(DOMAIN, dead_id)}) is None