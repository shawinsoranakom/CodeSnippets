async def test_no_fan_vacuum(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test status updates from the vacuum when fan is not supported."""
    await mqtt_mock_entry()

    message = """{
        "battery_level": 54,
        "state": "cleaning"
    }"""
    async_fire_mqtt_message(hass, "vacuum/state", message)
    state = hass.states.get("vacuum.mqtttest")
    assert state.state == VacuumActivity.CLEANING
    assert state.attributes.get(ATTR_FAN_SPEED) is None
    assert state.attributes.get(ATTR_FAN_SPEED_LIST) is None

    message = """{
        "battery_level": 54,
        "state": "cleaning",
        "fan_speed": "max"
    }"""
    async_fire_mqtt_message(hass, "vacuum/state", message)
    state = hass.states.get("vacuum.mqtttest")

    assert state.state == VacuumActivity.CLEANING
    assert state.attributes.get(ATTR_FAN_SPEED) is None
    assert state.attributes.get(ATTR_FAN_SPEED_LIST) is None

    message = """{
        "battery_level": 61,
        "state": "docked"
    }"""

    async_fire_mqtt_message(hass, "vacuum/state", message)
    state = hass.states.get("vacuum.mqtttest")
    assert state.state == VacuumActivity.DOCKED