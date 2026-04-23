async def test_binary_sensors_created(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_hikcamera: MagicMock,
) -> None:
    """Test binary sensors are created for each event type."""
    await setup_integration(hass, mock_config_entry)

    # Check Motion sensor (camera type doesn't include channel in name)
    state = hass.states.get("binary_sensor.front_camera_motion")
    assert state is not None
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_DEVICE_CLASS) == BinarySensorDeviceClass.MOTION
    assert ATTR_LAST_TRIP_TIME in state.attributes

    # Check Line Crossing sensor
    state = hass.states.get("binary_sensor.front_camera_line_crossing")
    assert state is not None
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_DEVICE_CLASS) == BinarySensorDeviceClass.MOTION