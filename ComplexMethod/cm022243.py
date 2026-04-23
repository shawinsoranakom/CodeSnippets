async def test_all_sensor_entities(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_cloud_interface: AsyncMock,
) -> None:
    """Test all entities."""

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)

    # There should be exactly three sensor entities
    sensor_entries = [
        entry
        for entry in entity_registry.entities.values()
        if entry.platform == "intelliclima" and entry.domain == SENSOR_DOMAIN
    ]
    assert len(sensor_entries) == 3

    entity_entry = sensor_entries[0]
    # Device should exist and match snapshot
    assert entity_entry.device_id
    assert (device_entry := device_registry.async_get(entity_entry.device_id))
    assert device_entry == snapshot