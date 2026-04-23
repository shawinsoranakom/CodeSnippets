async def test_forced_text_length(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a text entity that only allows a fixed length."""
    await mqtt_mock_entry()

    state = hass.states.get("text.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "state-topic", "12345")
    state = hass.states.get("text.test")
    assert state.state == "12345"

    caplog.clear()
    # Text too long
    async_fire_mqtt_message(hass, "state-topic", "123456")
    state = hass.states.get("text.test")
    assert state.state == "12345"
    assert (
        "Entity text.test provides state 123456 "
        "which is too long (maximum length 5)" in caplog.text
    )

    caplog.clear()
    # Text too short
    async_fire_mqtt_message(hass, "state-topic", "1")
    state = hass.states.get("text.test")
    assert state.state == "12345"
    assert (
        "Entity text.test provides state 1 "
        "which is too short (minimum length 5)" in caplog.text
    )
    # Valid update
    async_fire_mqtt_message(hass, "state-topic", "54321")
    state = hass.states.get("text.test")
    assert state.state == "54321"