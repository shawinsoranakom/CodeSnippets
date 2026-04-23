async def test_remove_config_subentry_from_device_removes_entities_2(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    subentries_in_device: list[str | None],
    subentry_in_entity: str | None,
) -> None:
    """Test that we don't remove entities with no config entry when device is modified."""
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
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-3",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
        ],
    )
    config_entry_1.add_to_hass(hass)

    # Create device with two config subentries
    device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id=subentries_in_device[0],
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        config_subentry_id=subentries_in_device[1],
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    assert device_entry.config_entries == {config_entry_1.entry_id}
    assert device_entry.config_entries_subentries == {
        config_entry_1.entry_id: set(subentries_in_device),
    }

    # Create an entity without config entry or subentry
    entry_1 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        device_id=device_entry.id,
    )
    # Create an entity for same config entry but subentry not in device
    entry_2 = entity_registry.async_get_or_create(
        "light",
        "some_helper",
        "5678",
        config_entry=config_entry_1,
        config_subentry_id=subentry_in_entity,
        device_id=device_entry.id,
    )
    # Create an entity for same config entry but subentry not in device
    entry_3 = entity_registry.async_get_or_create(
        "light",
        "some_helper",
        "abcd",
        config_entry=config_entry_1,
        config_subentry_id="mock-subentry-id-3",
        device_id=device_entry.id,
    )

    assert len({entry_1.entity_id, entry_2.entity_id, entry_3.entity_id}) == 3
    assert entity_registry.async_is_registered(entry_1.entity_id)
    assert entity_registry.async_is_registered(entry_2.entity_id)
    assert entity_registry.async_is_registered(entry_3.entity_id)

    # Remove the first config subentry from the device
    device_registry.async_update_device(
        device_entry.id,
        remove_config_entry_id=config_entry_1.entry_id,
        remove_config_subentry_id=subentries_in_device[0],
    )
    await hass.async_block_till_done()

    assert device_registry.async_get(device_entry.id)
    # Entities with a config subentry not in the device are not removed
    assert entity_registry.async_is_registered(entry_1.entity_id)
    assert entity_registry.async_is_registered(entry_2.entity_id)
    assert entity_registry.async_is_registered(entry_3.entity_id)

    # Remove the second config subentry from the device, this removes the device
    device_registry.async_update_device(
        device_entry.id,
        remove_config_entry_id=config_entry_1.entry_id,
        remove_config_subentry_id=subentries_in_device[1],
    )
    await hass.async_block_till_done()

    assert not device_registry.async_get(device_entry.id)
    # Entities with a config subentry not in the device are not removed
    assert entity_registry.async_is_registered(entry_1.entity_id)
    assert entity_registry.async_is_registered(entry_2.entity_id)
    assert entity_registry.async_is_registered(entry_3.entity_id)
    # Check the device link is set to None
    assert entity_registry.async_get(entry_1.entity_id).device_id is None
    assert entity_registry.async_get(entry_2.entity_id).device_id is None
    assert entity_registry.async_get(entry_3.entity_id).device_id is None