async def test_controlling_state_via_topic_and_json_message_shared_topic(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the controlling state via topic and JSON message using a shared topic."""
    await mqtt_mock_entry()

    state = hass.states.get("fan.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("direction") is None
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(
        hass,
        "shared-state-topic",
        """{
        "state":"ON",
        "preset_mode":"eco",
        "oscillation":"oscillate_on",
        "percentage": 50,
        "direction": "forward"
        }""",
    )
    state = hass.states.get("fan.test")
    assert state.state == STATE_ON
    assert state.attributes.get("direction") == "forward"
    assert state.attributes.get("oscillating") is True
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 50
    assert state.attributes.get("preset_mode") == "eco"

    async_fire_mqtt_message(
        hass,
        "shared-state-topic",
        """{
       "state":"ON",
       "preset_mode":"auto",
       "oscillation":"oscillate_off",
       "percentage": 10,
       "direction": "forward"
       }""",
    )
    state = hass.states.get("fan.test")
    assert state.state == STATE_ON
    assert state.attributes.get("direction") == "forward"
    assert state.attributes.get("oscillating") is False
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 10
    assert state.attributes.get("preset_mode") == "auto"

    async_fire_mqtt_message(
        hass,
        "shared-state-topic",
        """{
        "state":"OFF",
        "preset_mode":"auto",
        "oscillation":"oscillate_off",
        "percentage": 0,
        "direction": "reverse"
        }""",
    )
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get("direction") == "reverse"
    assert state.attributes.get("oscillating") is False
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 0
    assert state.attributes.get("preset_mode") == "auto"

    async_fire_mqtt_message(
        hass,
        "shared-state-topic",
        '{"percentage": 100}',
    )
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 100
    assert state.attributes.get("preset_mode") == "auto"
    caplog.clear()