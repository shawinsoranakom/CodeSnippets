async def test_has_entity_name_false_device_name_changes(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test device name changes update entities with has_entity_name=False."""
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        name="Hue Light",
    )

    entry = entity_registry.async_get_or_create(
        "light",
        "hue",
        "1",
        config_entry=config_entry,
        device_id=device_entry.id,
        has_entity_name=False,
        original_name="Hue Light Temperature",
    )
    assert entry.original_name_unprefixed == "Temperature"

    entry2 = entity_registry.async_get_or_create(
        "sensor",
        "hue",
        "2",
        config_entry=config_entry,
        device_id=device_entry.id,
        has_entity_name=False,
        original_name="Bulb brightness",
    )
    assert entry2.original_name_unprefixed is None

    entry3 = entity_registry.async_get_or_create(
        "sensor",
        "hue",
        "3",
        config_entry=config_entry,
        device_id=device_entry.id,
        has_entity_name=False,
        original_name="Bulb brightness",
    )
    entity_registry.async_update_entity(entry3.entity_id, name="My name")
    assert entry3.original_name_unprefixed is None

    entry4 = entity_registry.async_get_or_create(
        "sensor",
        "hue",
        "4",
        config_entry=config_entry,
        device_id=device_entry.id,
        has_entity_name=True,
        original_name="Hue Light Battery",
    )
    assert entry4.original_name_unprefixed is None

    # Integration renames device
    device_registry.async_update_device(device_entry.id, name="Something else")
    await hass.async_block_till_done()

    updated = entity_registry.async_get(entry.entity_id)
    assert updated.name is None
    assert updated.original_name_unprefixed is None

    updated2 = entity_registry.async_get(entry2.entity_id)
    assert updated2.name is None
    assert updated2.original_name_unprefixed is None

    updated3 = entity_registry.async_get(entry3.entity_id)
    assert updated3.name == "My name"
    assert updated3.original_name_unprefixed is None

    updated4 = entity_registry.async_get(entry4.entity_id)
    assert updated4.name is None
    assert updated4.original_name_unprefixed is None

    # Integration renames device to something else
    device_registry.async_update_device(device_entry.id, name="Bulb")
    await hass.async_block_till_done()

    updated = entity_registry.async_get(entry.entity_id)
    assert updated.name is None
    assert updated.original_name_unprefixed is None

    updated2 = entity_registry.async_get(entry2.entity_id)
    assert updated2.name is None
    assert updated2.original_name_unprefixed == "Brightness"

    updated3 = entity_registry.async_get(entry3.entity_id)
    assert updated3.name == "My name"
    assert updated3.original_name_unprefixed == "Brightness"

    updated4 = entity_registry.async_get(entry4.entity_id)
    assert updated4.name is None
    assert updated4.original_name_unprefixed is None

    # User renames device
    device_registry.async_update_device(device_entry.id, name_by_user="Hue")
    await hass.async_block_till_done()

    updated = entity_registry.async_get(entry.entity_id)
    assert updated.name is None
    assert updated.original_name_unprefixed == "Light Temperature"

    updated2 = entity_registry.async_get(entry2.entity_id)
    assert updated2.name == "Hue Brightness"
    assert updated2.original_name_unprefixed is None

    updated3 = entity_registry.async_get(entry3.entity_id)
    assert updated3.name == "My name"
    assert updated3.original_name_unprefixed is None

    updated4 = entity_registry.async_get(entry4.entity_id)
    assert updated4.name is None
    assert updated4.original_name_unprefixed is None