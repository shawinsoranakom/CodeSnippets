async def test_remove_config_entry_from_device_removes_entities_2(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that we don't remove entities with no config entry when device is modified."""
    config_entry_1 = MockConfigEntry(domain="hue")
    config_entry_1.add_to_hass(hass)
    config_entry_2 = MockConfigEntry(domain="device_tracker")
    config_entry_2.add_to_hass(hass)
    config_entry_3 = MockConfigEntry(domain="some_helper")
    config_entry_3.add_to_hass(hass)

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

    # Create an entity without config entry
    entry_1 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        device_id=device_entry.id,
    )
    # Create an entity with a config entry not in the device
    entry_2 = entity_registry.async_get_or_create(
        "light",
        "some_helper",
        "5678",
        config_entry=config_entry_3,
        device_id=device_entry.id,
    )

    assert entry_1.entity_id != entry_2.entity_id
    assert entity_registry.async_is_registered(entry_1.entity_id)
    assert entity_registry.async_is_registered(entry_2.entity_id)

    # Remove the first config entry from the device
    device_registry.async_update_device(
        device_entry.id, remove_config_entry_id=config_entry_1.entry_id
    )
    await hass.async_block_till_done()

    assert device_registry.async_get(device_entry.id)
    # Entities which are not tied to the removed config entry should not be removed
    assert entity_registry.async_is_registered(entry_1.entity_id)
    assert entity_registry.async_is_registered(entry_2.entity_id)

    # Remove the second config entry from the device (this removes the device)
    device_registry.async_update_device(
        device_entry.id, remove_config_entry_id=config_entry_2.entry_id
    )
    await hass.async_block_till_done()

    assert not device_registry.async_get(device_entry.id)
    # Entities which are not tied to a config entry in the device should not be removed
    assert entity_registry.async_is_registered(entry_1.entity_id)
    assert entity_registry.async_is_registered(entry_2.entity_id)
    # Check the device link is set to None
    assert entity_registry.async_get(entry_1.entity_id).device_id is None
    assert entity_registry.async_get(entry_2.entity_id).device_id is None