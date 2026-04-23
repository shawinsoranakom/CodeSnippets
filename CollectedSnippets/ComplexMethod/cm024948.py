async def test_remove_config_subentry_from_device_removes_entities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that we remove entities tied to a device when config subentry is removed."""
    config_entry_1 = MockConfigEntry(
        domain="hue",
        subentries_data=[
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-1",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-2",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
        ],
    )
    config_entry_1.add_to_hass(hass)

    # Create device with three config subentries
    device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id="mock-subentry-id-1",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id="mock-subentry-id-2",
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    assert device_entry.config_entries == {config_entry_1.entry_id}
    assert device_entry.config_entries_subentries == {
        config_entry_1.entry_id: {None, "mock-subentry-id-1", "mock-subentry-id-2"},
    }

    # Create one entity entry for each config entry or subentry
    entry_1 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "1234",
        config_entry=config_entry_1,
        config_subentry_id="mock-subentry-id-1",
        device_id=device_entry.id,
    )

    entry_2 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry_1,
        config_subentry_id="mock-subentry-id-2",
        device_id=device_entry.id,
    )

    entry_3 = entity_registry.async_get_or_create(
        "sensor",
        "device_tracker",
        "6789",
        config_entry=config_entry_1,
        config_subentry_id=None,
        device_id=device_entry.id,
    )

    assert entity_registry.async_is_registered(entry_1.entity_id)
    assert entity_registry.async_is_registered(entry_2.entity_id)
    assert entity_registry.async_is_registered(entry_3.entity_id)

    # Remove the first config subentry from the device, the entity associated with it
    # should be removed
    device_registry.async_update_device(
        device_entry.id,
        remove_config_entry_id=config_entry_1.entry_id,
        remove_config_subentry_id="mock-subentry-id-1",
    )
    await hass.async_block_till_done()

    assert device_registry.async_get(device_entry.id)
    assert not entity_registry.async_is_registered(entry_1.entity_id)
    assert entity_registry.async_is_registered(entry_2.entity_id)
    assert entity_registry.async_is_registered(entry_3.entity_id)

    # Remove the second config subentry from the device, the entity associated with it
    # should be removed
    device_registry.async_update_device(
        device_entry.id,
        remove_config_entry_id=config_entry_1.entry_id,
        remove_config_subentry_id=None,
    )
    await hass.async_block_till_done()

    assert device_registry.async_get(device_entry.id)
    assert not entity_registry.async_is_registered(entry_1.entity_id)
    assert entity_registry.async_is_registered(entry_2.entity_id)
    assert not entity_registry.async_is_registered(entry_3.entity_id)

    # Remove the third config subentry from the device, the entity associated with it
    # (and the device itself) should be removed
    device_registry.async_update_device(
        device_entry.id,
        remove_config_entry_id=config_entry_1.entry_id,
        remove_config_subentry_id="mock-subentry-id-2",
    )
    await hass.async_block_till_done()

    assert not device_registry.async_get(device_entry.id)
    assert not entity_registry.async_is_registered(entry_1.entity_id)
    assert not entity_registry.async_is_registered(entry_2.entity_id)
    assert not entity_registry.async_is_registered(entry_3.entity_id)