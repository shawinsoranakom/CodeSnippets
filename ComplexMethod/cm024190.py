async def test_invalid_sensor_value_via_mqtt_message(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the setting of the value via MQTT."""
    await mqtt_mock_entry()

    state = hass.states.get("binary_sensor.test")

    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "test-topic", "0N")
    state = hass.states.get("binary_sensor.test")
    assert state.state == STATE_UNKNOWN
    assert "No matching payload found for entity" in caplog.text
    caplog.clear()
    assert "No matching payload found for entity" not in caplog.text

    async_fire_mqtt_message(hass, "test-topic", "ON")
    state = hass.states.get("binary_sensor.test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "test-topic", "0FF")
    state = hass.states.get("binary_sensor.test")
    assert state.state == STATE_ON
    assert "No matching payload found for entity" in caplog.text