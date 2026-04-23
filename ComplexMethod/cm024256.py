async def test_status(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test status updates from the vacuum."""
    await mqtt_mock_entry()
    state = hass.states.get("vacuum.mqtttest")
    assert state.state == STATE_UNKNOWN

    message = """{
        "battery_level": 54,
        "state": "cleaning",
        "fan_speed": "max"
    }"""
    async_fire_mqtt_message(hass, "vacuum/state", message)
    state = hass.states.get("vacuum.mqtttest")
    assert state.state == VacuumActivity.CLEANING
    assert state.attributes.get(ATTR_FAN_SPEED) == "max"

    message = """{
        "battery_level": 61,
        "state": "docked",
        "fan_speed": "min"
    }"""

    async_fire_mqtt_message(hass, "vacuum/state", message)
    state = hass.states.get("vacuum.mqtttest")
    assert state.state == VacuumActivity.DOCKED
    assert state.attributes.get(ATTR_FAN_SPEED) == "min"
    assert state.attributes.get(ATTR_FAN_SPEED_LIST) == ["min", "medium", "high", "max"]

    message = '{"state":null}'
    async_fire_mqtt_message(hass, "vacuum/state", message)
    state = hass.states.get("vacuum.mqtttest")
    assert state.state == STATE_UNKNOWN