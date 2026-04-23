async def test_rain_sensor_device_association(
    hass: HomeAssistant,
    mock_window: MagicMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: EntityRegistry,
    device_registry: DeviceRegistry,
) -> None:
    """Test the rain sensor is properly associated with its device."""

    test_entity_id = "binary_sensor.test_window_rain_sensor"

    # Verify entity exists
    state = hass.states.get(test_entity_id)
    assert state is not None

    # Get entity entry
    entity_entry = entity_registry.async_get(test_entity_id)
    assert entity_entry is not None
    assert entity_entry.device_id is not None

    # Get device entry
    device_entry = device_registry.async_get(entity_entry.device_id)
    assert device_entry is not None

    # Verify device has correct identifiers
    assert ("velux", mock_window.serial_number) in device_entry.identifiers
    assert device_entry.name == mock_window.name

    # Verify via_device is gateway
    assert device_entry.via_device_id is not None
    via_device_entry = device_registry.async_get(device_entry.via_device_id)
    assert via_device_entry is not None
    assert via_device_entry.identifiers == {
        (DOMAIN, f"gateway_{mock_config_entry.entry_id}")
    }