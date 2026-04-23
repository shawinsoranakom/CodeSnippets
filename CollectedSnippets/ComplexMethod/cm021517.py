async def test_off_action_with_transition(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test off action with transition."""
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.state == STATE_ON
    assert state.attributes["color_mode"] == ColorMode.BRIGHTNESS
    assert state.attributes["supported_color_modes"] == [ColorMode.BRIGHTNESS]
    assert state.attributes["supported_features"] == LightEntityFeature.TRANSITION

    await _call_and_assert_action(
        hass, calls, SERVICE_TURN_OFF, {ATTR_TRANSITION: 2}, {ATTR_TRANSITION: 2}
    )

    assert state.state == STATE_ON
    assert state.attributes["color_mode"] == ColorMode.BRIGHTNESS
    assert state.attributes["supported_color_modes"] == [ColorMode.BRIGHTNESS]
    assert state.attributes["supported_features"] == LightEntityFeature.TRANSITION