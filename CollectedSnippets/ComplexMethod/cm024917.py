async def test_remove_stale_device_links_keep_entity_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test cleaning works for entity."""
    helper_config_entry = MockConfigEntry(domain="helper_integration")
    helper_config_entry.add_to_hass(hass)
    host_config_entry = MockConfigEntry(domain="host_integration")
    host_config_entry.add_to_hass(hass)

    current_device = device_registry.async_get_or_create(
        identifiers={("test", "current_device")},
        connections={("mac", "30:31:32:33:34:00")},
        config_entry_id=helper_config_entry.entry_id,
    )

    stale_device_1 = device_registry.async_get_or_create(
        identifiers={("test", "stale_device_1")},
        connections={("mac", "30:31:32:33:34:01")},
        config_entry_id=helper_config_entry.entry_id,
    )

    device_registry.async_get_or_create(
        identifiers={("test", "stale_device_2")},
        connections={("mac", "30:31:32:33:34:02")},
        config_entry_id=helper_config_entry.entry_id,
    )

    # Source entity
    source_entity = entity_registry.async_get_or_create(
        "sensor",
        "host_integration",
        "source",
        config_entry=host_config_entry,
        device_id=current_device.id,
    )
    assert entity_registry.async_get(source_entity.entity_id) is not None

    # Helper entity connected to a stale device
    helper_entity = entity_registry.async_get_or_create(
        "sensor",
        "helper_integration",
        "helper",
        config_entry=helper_config_entry,
        device_id=stale_device_1.id,
    )
    assert entity_registry.async_get(helper_entity.entity_id) is not None

    devices_helper_entry = device_registry.devices.get_devices_for_config_entry_id(
        helper_config_entry.entry_id
    )

    # 3 devices linked to the config entry are expected (1 current device + 2 stales)
    assert len(devices_helper_entry) == 3

    # Manual cleanup should unlink stale devices from the config entry
    async_remove_stale_devices_links_keep_entity_device(
        hass,
        entry_id=helper_config_entry.entry_id,
        source_entity_id_or_uuid=source_entity.entity_id,
    )

    await hass.async_block_till_done()

    devices_helper_entry = device_registry.devices.get_devices_for_config_entry_id(
        helper_config_entry.entry_id
    )

    # After cleanup, only one device is expected to be linked to the config entry, and
    # the entities should exist and be linked to the current device
    assert len(devices_helper_entry) == 1
    assert current_device in devices_helper_entry
    assert entity_registry.async_get(source_entity.entity_id) is not None
    assert entity_registry.async_get(helper_entity.entity_id) is not None