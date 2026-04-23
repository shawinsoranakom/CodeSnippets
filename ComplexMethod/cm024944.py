async def test_update_entity_recalculates_original_name_unprefixed(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test original_name_unprefixed is recalculated when relevant fields change."""
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)

    device1 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        name="Device Bla",
    )
    device2 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "AB:CD:EF:12:34:56")},
        name="Other",
    )

    entry = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device1.id,
        has_entity_name=False,
        original_name="Device Bla Sensor",
    )
    assert entry.original_name_unprefixed == "Sensor"

    entry = entity_registry.async_update_entity(
        entry.entity_id, original_name="Device Bla Temperature"
    )
    assert entry.original_name_unprefixed == "Temperature"

    entry = entity_registry.async_update_entity(
        entry.entity_id, original_name="Something Else"
    )
    assert entry.original_name_unprefixed is None

    entry = entity_registry.async_update_entity(
        entry.entity_id, original_name="Other Sensor"
    )
    assert entry.original_name_unprefixed is None

    entry = entity_registry.async_update_entity(entry.entity_id, device_id=device2.id)
    assert entry.original_name_unprefixed == "Sensor"

    entry = entity_registry.async_update_entity(
        entry.entity_id, original_name="Device Bla Sensor"
    )
    assert entry.original_name_unprefixed is None

    entry = entity_registry.async_update_entity(entry.entity_id, device_id=device1.id)
    assert entry.original_name_unprefixed == "Sensor"

    entry = entity_registry.async_update_entity(entry.entity_id, has_entity_name=True)
    assert entry.original_name_unprefixed is None