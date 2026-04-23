async def test_controlling_state_via_topic_no_percentage_topics(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the controlling state via topic without percentage topics."""
    await mqtt_mock_entry()

    state = hass.states.get("fan.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "preset-mode-state-topic", "smart")
    state = hass.states.get("fan.test")
    assert state.attributes.get("preset_mode") == "smart"
    assert state.attributes.get(fan.ATTR_PERCENTAGE) is None

    async_fire_mqtt_message(hass, "preset-mode-state-topic", "auto")
    state = hass.states.get("fan.test")
    assert state.attributes.get("preset_mode") == "auto"
    assert state.attributes.get(fan.ATTR_PERCENTAGE) is None

    async_fire_mqtt_message(hass, "preset-mode-state-topic", "whoosh")
    state = hass.states.get("fan.test")
    assert state.attributes.get("preset_mode") == "whoosh"
    assert state.attributes.get(fan.ATTR_PERCENTAGE) is None

    async_fire_mqtt_message(hass, "preset-mode-state-topic", "medium")
    assert "not a valid preset mode" in caplog.text
    caplog.clear()

    async_fire_mqtt_message(hass, "preset-mode-state-topic", "low")
    assert "not a valid preset mode" in caplog.text
    caplog.clear()