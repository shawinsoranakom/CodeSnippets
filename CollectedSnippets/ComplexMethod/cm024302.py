async def test_state_and_position_topics_state_not_set_via_position_topic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test state is not set via position topic when both state and position topics are set."""
    await mqtt_mock_entry()

    state = hass.states.get("cover.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "state-topic", "OPEN")

    state = hass.states.get("cover.test")
    assert state.state == CoverState.OPEN

    async_fire_mqtt_message(hass, "get-position-topic", "0")

    state = hass.states.get("cover.test")
    assert state.state == CoverState.OPEN

    async_fire_mqtt_message(hass, "get-position-topic", "100")

    state = hass.states.get("cover.test")
    assert state.state == CoverState.OPEN

    async_fire_mqtt_message(hass, "state-topic", "CLOSE")

    state = hass.states.get("cover.test")
    assert state.state == CoverState.CLOSED

    async_fire_mqtt_message(hass, "get-position-topic", "0")

    state = hass.states.get("cover.test")
    assert state.state == CoverState.CLOSED

    async_fire_mqtt_message(hass, "get-position-topic", "100")

    state = hass.states.get("cover.test")
    assert state.state == CoverState.CLOSED