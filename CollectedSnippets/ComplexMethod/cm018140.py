async def test_multi_sensor_readings(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test for multiple sensors in one household."""
    await setup_platform(hass, aioclient_mock, SENSOR_DOMAIN, MULTI_SENSOR_TOKEN)
    state = hass.states.get("sensor.efergy_power_usage_728386")
    assert state.state == "218"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.WATT
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT
    state = hass.states.get("sensor.efergy_power_usage_0")
    assert state.state == "1808"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.WATT
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT
    state = hass.states.get("sensor.efergy_power_usage_728387")
    assert state.state == "312"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfPower.WATT
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT