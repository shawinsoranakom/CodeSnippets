async def test_setting_numeric_sensor_native_value_handling_via_mqtt_message(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test the setting of a numeric sensor value via MQTT."""
    await hass.async_block_till_done()
    await mqtt_mock_entry()

    # float value
    async_fire_mqtt_message(hass, "test-topic", '{ "power": 45.3, "current": 5.24 }')
    state = hass.states.get("sensor.test")
    assert state.attributes.get("device_class") == "power"
    assert state.state == "45.3"

    # null value, native value should be None
    async_fire_mqtt_message(hass, "test-topic", '{ "power": null, "current": 5.34 }')
    state = hass.states.get("sensor.test")
    assert state.state == "unknown"

    # int value
    async_fire_mqtt_message(hass, "test-topic", '{ "power": 20, "current": 5.34 }')
    state = hass.states.get("sensor.test")
    assert state.state == "20"

    # int value
    async_fire_mqtt_message(hass, "test-topic", '{ "power": "21", "current": 5.34 }')
    state = hass.states.get("sensor.test")
    assert state.state == "21"

    # ignore empty value, native sensor value should not change
    async_fire_mqtt_message(hass, "test-topic", '{ "power": "", "current": 5.34 }')
    state = hass.states.get("sensor.test")
    assert state.state == "21"

    # omitting value, causing it to be ignored, native sensor value should not change (template warning will be logged though)
    async_fire_mqtt_message(hass, "test-topic", '{ "current": 5.34 }')
    state = hass.states.get("sensor.test")
    assert state.state == "21"