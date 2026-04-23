async def test_on_action_optimistic(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test on action with optimistic state."""
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.state == STATE_UNKNOWN
    assert state.attributes["color_mode"] is None
    assert state.attributes["supported_color_modes"] == [ColorMode.BRIGHTNESS]
    assert state.attributes["supported_features"] == 0

    await _call_and_assert_action(hass, calls, SERVICE_TURN_ON)

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.state == STATE_ON
    assert state.attributes["color_mode"] == ColorMode.BRIGHTNESS
    assert state.attributes["supported_color_modes"] == [ColorMode.BRIGHTNESS]
    assert state.attributes["supported_features"] == 0

    await _call_and_assert_action(
        hass,
        calls,
        SERVICE_TURN_ON,
        {ATTR_BRIGHTNESS: 100},
        {ATTR_BRIGHTNESS: 100},
        "set_level",
    )

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.state == STATE_ON
    assert state.attributes["color_mode"] == ColorMode.BRIGHTNESS
    assert state.attributes["supported_color_modes"] == [ColorMode.BRIGHTNESS]
    assert state.attributes["supported_features"] == 0