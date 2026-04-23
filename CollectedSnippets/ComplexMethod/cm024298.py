async def test_controlling_validation_state_via_topic(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the validation of a received state."""
    await mqtt_mock_entry()

    state = hass.states.get("text.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes[text.ATTR_MODE] == "text"

    async_fire_mqtt_message(hass, "state-topic", "yes")
    state = hass.states.get("text.test")
    assert state.state == "yes"

    # test pattern error
    caplog.clear()
    async_fire_mqtt_message(hass, "state-topic", "other")
    await hass.async_block_till_done()
    assert (
        "Entity text.test provides state other which does not match expected pattern (y|n)"
        in caplog.text
    )
    state = hass.states.get("text.test")
    assert state.state == "yes"

    # test text size to large
    caplog.clear()
    async_fire_mqtt_message(hass, "state-topic", "yesyesyesyes")
    await hass.async_block_till_done()
    assert (
        "Entity text.test provides state yesyesyesyes which is too long (maximum length 10)"
        in caplog.text
    )
    state = hass.states.get("text.test")
    assert state.state == "yes"

    # test text size to small
    caplog.clear()
    async_fire_mqtt_message(hass, "state-topic", "y")
    await hass.async_block_till_done()
    assert (
        "Entity text.test provides state y which is too short (minimum length 2)"
        in caplog.text
    )
    state = hass.states.get("text.test")
    assert state.state == "yes"

    # test with valid text
    async_fire_mqtt_message(hass, "state-topic", "no")
    await hass.async_block_till_done()
    state = hass.states.get("text.test")
    assert state.state == "no"