async def test_attributes(hass: HomeAssistant) -> None:
    """Test the sensor attributes are correct."""
    await setup_platform(hass, SENSOR_DOMAIN)

    state = hass.states.get("sensor.environment_sensor_humidity")
    assert state.state == "32.0"
    assert state.attributes.get(ATTR_DEVICE_ID) == "RF:02148e70"
    assert not state.attributes.get("battery_low")
    assert not state.attributes.get("no_response")
    assert state.attributes.get("device_type") == "LM"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Environment Sensor Humidity"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.HUMIDITY
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.environment_sensor_illuminance")
    assert state.state == "1.0"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == "lx"
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT

    state = hass.states.get("sensor.environment_sensor_temperature")
    # Abodepy device JSON reports 19.5, but Home Assistant shows 19.4
    assert float(state.state) == pytest.approx(19.44444)
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS
    assert state.attributes.get(ATTR_STATE_CLASS) == SensorStateClass.MEASUREMENT