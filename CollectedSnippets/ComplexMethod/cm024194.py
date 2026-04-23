async def test_valid_device_class_and_uom(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test device_class option with valid values and test with an empty unit of measurement."""
    await mqtt_mock_entry()

    state = hass.states.get("sensor.test_1")
    assert state is not None
    assert state.attributes["device_class"] == "temperature"
    state = hass.states.get("sensor.test_2")
    assert state is not None
    assert "device_class" not in state.attributes
    state = hass.states.get("sensor.test_3")
    assert state is not None
    assert "device_class" not in state.attributes
    state = hass.states.get("sensor.test_4")
    assert state is not None
    assert state.attributes["device_class"] == "ph"
    state = hass.states.get("sensor.test_5")
    assert state is not None
    assert state.attributes["device_class"] == "ph"
    state = hass.states.get("sensor.test_6")
    assert state is not None
    assert "device_class" not in state.attributes
    state = hass.states.get("sensor.test_7")
    assert state is not None
    assert "device_class" not in state.attributes