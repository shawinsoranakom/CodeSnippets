async def test_controlling_state_via_topic_and_json_message(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the controlling state via topic and JSON message (percentage mode)."""
    await mqtt_mock_entry()

    state = hass.states.get("fan.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "state-topic", '{"val":"ON"}')
    state = hass.states.get("fan.test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "state-topic", '{"val": null}')
    state = hass.states.get("fan.test")
    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "state-topic", '{"val":"OFF"}')
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get("oscillating") is False

    async_fire_mqtt_message(hass, "direction-state-topic", '{"val":"forward"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("direction") == "forward"

    async_fire_mqtt_message(hass, "direction-state-topic", '{"val":"reverse"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("direction") == "reverse"

    async_fire_mqtt_message(hass, "oscillation-state-topic", '{"val":"oscillate_on"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("oscillating") is True

    async_fire_mqtt_message(hass, "oscillation-state-topic", '{"val":"oscillate_off"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("oscillating") is False

    async_fire_mqtt_message(hass, "percentage-state-topic", '{"val": 1}')
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 1

    async_fire_mqtt_message(hass, "percentage-state-topic", '{"val": 100}')
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 100

    async_fire_mqtt_message(hass, "percentage-state-topic", '{"val": "None"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PERCENTAGE) is None

    async_fire_mqtt_message(hass, "percentage-state-topic", '{"otherval": 100}')
    assert state.attributes.get(fan.ATTR_PERCENTAGE) is None
    caplog.clear()

    async_fire_mqtt_message(hass, "preset-mode-state-topic", '{"val": "low"}')
    assert "not a valid preset mode" in caplog.text
    caplog.clear()

    async_fire_mqtt_message(hass, "preset-mode-state-topic", '{"val": "auto"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("preset_mode") == "auto"

    async_fire_mqtt_message(hass, "preset-mode-state-topic", '{"val": "breeze"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("preset_mode") == "breeze"

    async_fire_mqtt_message(hass, "preset-mode-state-topic", '{"val": "silent"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("preset_mode") == "silent"

    async_fire_mqtt_message(hass, "preset-mode-state-topic", '{"val": "None"}')
    state = hass.states.get("fan.test")
    assert state.attributes.get("preset_mode") is None

    async_fire_mqtt_message(hass, "preset-mode-state-topic", '{"otherval": 100}')
    assert state.attributes.get("preset_mode") is None