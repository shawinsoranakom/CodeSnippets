async def test_set_state_via_position_using_stopped_state(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the controlling state via position topic using stopped state."""
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

    async_fire_mqtt_message(hass, "state-topic", "STOPPED")

    state = hass.states.get("cover.test")
    assert state.state == CoverState.CLOSED

    async_fire_mqtt_message(hass, "get-position-topic", "100")

    state = hass.states.get("cover.test")
    assert state.state == CoverState.CLOSED

    async_fire_mqtt_message(hass, "state-topic", "STOPPED")

    state = hass.states.get("cover.test")
    assert state.state == CoverState.OPEN