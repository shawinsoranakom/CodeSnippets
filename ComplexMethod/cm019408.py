async def test_zone_sensor_unique_ids(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_atw_device: MagicMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test unique ID generation for zone sensors with multiple zones."""
    zone_2 = MagicMock()
    zone_2.zone_index = 2
    zone_2.name = "Zone 2"
    zone_2.room_temperature = 23.5
    zone_2.zone_flow_temperature = 37.0
    zone_2.zone_return_temperature = 32.0
    mock_atw_device.zones = [mock_atw_device.zones[0], zone_2]

    await setup_platform(hass, mock_config_entry, [Platform.SENSOR])

    # Zone 1 sensors - no zone suffix in unique ID
    entry = entity_registry.async_get("sensor.ecodan_zone_1_room_temperature")
    assert entry is not None
    assert entry.unique_id == f"{MOCK_SERIAL}-{MOCK_MAC}-room_temperature"

    entry = entity_registry.async_get("sensor.ecodan_zone_1_flow_temperature")
    assert entry is not None
    assert entry.unique_id == f"{MOCK_SERIAL}-{MOCK_MAC}-flow_temperature"

    entry = entity_registry.async_get("sensor.ecodan_zone_1_return_temperature")
    assert entry is not None
    assert entry.unique_id == f"{MOCK_SERIAL}-{MOCK_MAC}-return_temperature"

    # Zone 2 sensors - with zone suffix in unique ID
    entry = entity_registry.async_get("sensor.ecodan_zone_2_room_temperature")
    assert entry is not None
    assert entry.unique_id == f"{MOCK_SERIAL}-{MOCK_MAC}-room_temperature-zone-2"

    entry = entity_registry.async_get("sensor.ecodan_zone_2_flow_temperature")
    assert entry is not None
    assert entry.unique_id == f"{MOCK_SERIAL}-{MOCK_MAC}-flow_temperature-zone-2"

    entry = entity_registry.async_get("sensor.ecodan_zone_2_return_temperature")
    assert entry is not None
    assert entry.unique_id == f"{MOCK_SERIAL}-{MOCK_MAC}-return_temperature-zone-2"