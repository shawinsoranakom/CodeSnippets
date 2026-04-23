async def test_sensor_type_output(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, mock_iotawatt: MagicMock
) -> None:
    """Tests the sensor type of Output."""
    mock_iotawatt.getSensors.return_value["sensors"]["my_watthour_sensor_key"] = (
        OUTPUT_SENSOR
    )
    assert await async_setup_component(hass, "iotawatt", {})
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids()) == 1

    state = hass.states.get("sensor.my_watthour_sensor")
    assert state is not None
    assert state.state == "243"
    assert state.attributes[ATTR_STATE_CLASS] is SensorStateClass.TOTAL
    assert state.attributes[ATTR_FRIENDLY_NAME] == "My WattHour Sensor"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfEnergy.WATT_HOUR
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENERGY
    assert state.attributes["type"] == "Output"

    mock_iotawatt.getSensors.return_value["sensors"].pop("my_watthour_sensor_key")
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.my_watthour_sensor") is None