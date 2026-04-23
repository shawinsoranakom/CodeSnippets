async def test_remove_config_entry_from_device_removes_entities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that we remove entities tied to a device when config entry is removed."""
    config_entry_1 = MockConfigEntry(domain="hue")
    config_entry_1.add_to_hass(hass)
    config_entry_2 = MockConfigEntry(domain="device_tracker")
    config_entry_2.add_to_hass(hass)

    # Create device with two config entries
    device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_2.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    assert device_entry.config_entries == {
        config_entry_1.entry_id,
        config_entry_2.entry_id,
    }

    # Create one entity for each config entry
    entry_1 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry_1,
        device_id=device_entry.id,
    )

    entry_2 = entity_registry.async_get_or_create(
        "sensor",
        "device_tracker",
        "6789",
        config_entry=config_entry_2,
        device_id=device_entry.id,
    )

    assert entity_registry.async_is_registered(entry_1.entity_id)
    assert entity_registry.async_is_registered(entry_2.entity_id)

    # Remove the first config entry from the device, the entity associated with it
    # should be removed
    device_registry.async_update_device(
        device_entry.id, remove_config_entry_id=config_entry_1.entry_id
    )
    await hass.async_block_till_done()

    assert device_registry.async_get(device_entry.id)
    assert not entity_registry.async_is_registered(entry_1.entity_id)
    assert entity_registry.async_is_registered(entry_2.entity_id)

    # Remove the second config entry from the device, the entity associated with it
    # (and the device itself) should be removed
    device_registry.async_update_device(
        device_entry.id, remove_config_entry_id=config_entry_2.entry_id
    )
    await hass.async_block_till_done()

    assert not device_registry.async_get(device_entry.id)
    assert not entity_registry.async_is_registered(entry_1.entity_id)
    assert not entity_registry.async_is_registered(entry_2.entity_id)