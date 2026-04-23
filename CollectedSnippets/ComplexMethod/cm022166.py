async def test_gps_sensor(
    hass: HomeAssistant,
    gps_sensor: Sensor,
    receive_message: Callable[[str], None],
) -> None:
    """Test a gps sensor."""
    entity_id = "device_tracker.gps_sensor_1_1"
    altitude = 0
    latitude = "40.742"
    longitude = "-73.989"
    message_string = f"1;1;1;0;49;{latitude},{longitude},{altitude}\n"

    receive_message(message_string)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == STATE_NOT_HOME
    assert state.attributes[ATTR_SOURCE_TYPE] == SourceType.GPS
    assert state.attributes[ATTR_LATITUDE] == float(latitude)
    assert state.attributes[ATTR_LONGITUDE] == float(longitude)
    assert state.attributes[ATTR_BATTERY_LEVEL] == 0

    latitude = "40.782"
    longitude = "-73.965"
    message_string = f"1;1;1;0;49;{latitude},{longitude},{altitude}\n"

    receive_message(message_string)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == STATE_NOT_HOME
    assert state.attributes[ATTR_SOURCE_TYPE] == SourceType.GPS
    assert state.attributes[ATTR_LATITUDE] == float(latitude)
    assert state.attributes[ATTR_LONGITUDE] == float(longitude)