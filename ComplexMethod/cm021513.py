async def test_on_action(hass: HomeAssistant, calls: list[ServiceCall]) -> None:
    """Test on action."""
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.state == STATE_OFF
    assert state.attributes["color_mode"] is None
    assert state.attributes["supported_color_modes"] == [ColorMode.BRIGHTNESS]
    assert state.attributes["supported_features"] == 0

    await _call_and_assert_action(hass, calls, SERVICE_TURN_ON)

    assert state.state == STATE_OFF
    assert state.attributes["color_mode"] is None
    assert state.attributes["supported_color_modes"] == [ColorMode.BRIGHTNESS]
    assert state.attributes["supported_features"] == 0