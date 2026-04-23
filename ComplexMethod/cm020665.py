async def test_async_new_device_discovery(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    manager: VeSync,
    fan,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test new device discovery."""

    # Entry should not be set up yet; we'll install a fan before setup
    assert config_entry.state is ConfigEntryState.NOT_LOADED

    # Set up the config entry (no devices initially)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    # Simulate the manager discovering a new fan when get_devices is called
    manager.get_devices = AsyncMock(
        side_effect=lambda: manager._dev_list["fans"].append(fan)
    )

    # Call the service that should trigger discovery and platform setup
    await hass.services.async_call(DOMAIN, SERVICE_UPDATE_DEVS, {}, blocking=True)
    await hass.async_block_till_done()

    assert manager.get_devices.call_count == 1

    # Verify an entity for the new fan was created in Home Assistant
    fan_entry = next(
        (
            e
            for e in entity_registry.entities.values()
            if e.unique_id == fan.cid and e.domain == "fan"
        ),
        None,
    )
    assert fan_entry is not None