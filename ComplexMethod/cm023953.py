async def test_registry_cleanup(
    hass: HomeAssistant,
    load_int: ConfigEntry,
    hass_ws_client: WebSocketGenerator,
    unit_count: int,
) -> None:
    """Test being able to remove a disconnected device."""
    entry_id = load_int.entry_id
    device_registry = dr.async_get(hass)
    live_id = "L1.100"
    dead_id = "L2.200"

    assert (
        len(dr.async_entries_for_config_entry(device_registry, entry_id)) == unit_count
    )
    device_registry.async_get_or_create(
        config_entry_id=entry_id,
        identifiers={(DOMAIN, dead_id)},
        manufacturer="CoolAutomation",
        model="CoolMasterNet",
        name=dead_id,
        sw_version="1.0",
    )

    assert (
        len(dr.async_entries_for_config_entry(device_registry, entry_id))
        == unit_count + 1
    )

    assert await async_setup_component(hass, "config", {})
    client = await hass_ws_client(hass)
    # Try to remove "L1.100" - fails since it is live
    device = device_registry.async_get_device(identifiers={(DOMAIN, live_id)})
    assert device is not None
    response = await client.remove_device(device.id, entry_id)
    assert not response["success"]
    assert (
        len(dr.async_entries_for_config_entry(device_registry, entry_id))
        == unit_count + 1
    )
    assert device_registry.async_get_device(identifiers={(DOMAIN, live_id)}) is not None

    # Try to remove "L2.200" - succeeds since it is dead
    device = device_registry.async_get_device(identifiers={(DOMAIN, dead_id)})
    assert device is not None
    response = await client.remove_device(device.id, entry_id)
    assert response["success"]
    assert (
        len(dr.async_entries_for_config_entry(device_registry, entry_id)) == unit_count
    )
    assert device_registry.async_get_device(identifiers={(DOMAIN, dead_id)}) is None