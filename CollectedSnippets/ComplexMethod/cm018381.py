async def test_sensor_type_input(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, mock_iotawatt: MagicMock
) -> None:
    """Test input sensors work."""
    assert await async_setup_component(hass, "iotawatt", {})
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids()) == 0

    # Discover this sensor during a regular update.
    mock_iotawatt.getSensors.return_value["sensors"]["my_sensor_key"] = INPUT_SENSOR
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids()) == 1

    state = hass.states.get("sensor.test_device_my_sensor")
    assert state is not None
    assert state.state == "23"
    assert state.attributes[ATTR_STATE_CLASS] is SensorStateClass.MEASUREMENT
    assert state.attributes[ATTR_FRIENDLY_NAME] == "Test Device My Sensor"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfPower.WATT
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.POWER
    assert state.attributes["channel"] == "1"
    assert state.attributes["type"] == "Input"

    mock_iotawatt.getSensors.return_value["sensors"].pop("my_sensor_key")
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.test_device_my_sensor") is None