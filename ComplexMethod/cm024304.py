async def test_controlling_state_via_topic(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the controlling state via topic."""
    await mqtt_mock_entry()

    state = hass.states.get("fan.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "state-topic", "StAtE_On")
    state = hass.states.get("fan.test")
    assert state.state == STATE_ON

    async_fire_mqtt_message(hass, "state-topic", "StAtE_OfF")
    state = hass.states.get("fan.test")
    assert state.state == STATE_OFF
    assert state.attributes.get("oscillating") is False

    async_fire_mqtt_message(hass, "direction-state-topic", "forward")
    state = hass.states.get("fan.test")
    assert state.attributes.get("direction") == "forward"

    async_fire_mqtt_message(hass, "direction-state-topic", "reverse")
    state = hass.states.get("fan.test")
    assert state.attributes.get("direction") == "reverse"

    async_fire_mqtt_message(hass, "oscillation-state-topic", "OsC_On")
    state = hass.states.get("fan.test")
    assert state.attributes.get("oscillating") is True

    async_fire_mqtt_message(hass, "oscillation-state-topic", "OsC_OfF")
    state = hass.states.get("fan.test")
    assert state.attributes.get("oscillating") is False

    assert state.attributes.get("percentage_step") == 1.0

    async_fire_mqtt_message(hass, "percentage-state-topic", "0")
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 0

    async_fire_mqtt_message(hass, "percentage-state-topic", "50")
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 25

    async_fire_mqtt_message(hass, "percentage-state-topic", "100")
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 50

    async_fire_mqtt_message(hass, "percentage-state-topic", "200")
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PERCENTAGE) == 100

    async_fire_mqtt_message(hass, "percentage-state-topic", "202")
    assert "not a valid speed within the speed range" in caplog.text
    caplog.clear()

    async_fire_mqtt_message(hass, "percentage-state-topic", "invalid")
    assert "not a valid speed within the speed range" in caplog.text
    caplog.clear()

    async_fire_mqtt_message(hass, "preset-mode-state-topic", "low")
    assert "not a valid preset mode" in caplog.text
    caplog.clear()

    async_fire_mqtt_message(hass, "preset-mode-state-topic", "auto")
    state = hass.states.get("fan.test")
    assert state.attributes.get("preset_mode") == "auto"

    async_fire_mqtt_message(hass, "preset-mode-state-topic", "eco")
    state = hass.states.get("fan.test")
    assert state.attributes.get("preset_mode") == "eco"

    async_fire_mqtt_message(hass, "preset-mode-state-topic", "silent")
    state = hass.states.get("fan.test")
    assert state.attributes.get("preset_mode") == "silent"

    async_fire_mqtt_message(hass, "preset-mode-state-topic", "rEset_preset_mode")
    state = hass.states.get("fan.test")
    assert state.attributes.get("preset_mode") is None

    async_fire_mqtt_message(hass, "preset-mode-state-topic", "ModeUnknown")
    assert "not a valid preset mode" in caplog.text
    caplog.clear()

    async_fire_mqtt_message(hass, "percentage-state-topic", "rEset_percentage")
    state = hass.states.get("fan.test")
    assert state.attributes.get(fan.ATTR_PERCENTAGE) is None

    async_fire_mqtt_message(hass, "state-topic", "None")
    state = hass.states.get("fan.test")
    assert state.state == STATE_UNKNOWN