async def test_all_fan_entities(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_cloud_interface: AsyncMock,
) -> None:
    """Test all entities."""

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)

    # There should be exactly one fan entity
    fan_entries = [
        entry
        for entry in entity_registry.entities.values()
        if entry.platform == "intelliclima" and entry.domain == FAN_DOMAIN
    ]
    assert len(fan_entries) == 1
    entity_entry = fan_entries[0]

    # Device should exist and match snapshot
    assert entity_entry.device_id
    assert (device_entry := device_registry.async_get(entity_entry.device_id))
    assert device_entry == snapshot