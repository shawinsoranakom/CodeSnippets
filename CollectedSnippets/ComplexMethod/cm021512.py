async def test_template_state_text(hass: HomeAssistant) -> None:
    """Test the state text of a template."""
    set_state = STATE_ON
    await async_trigger(hass, TEST_STATE_ENTITY_ID, set_state)
    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.state == set_state
    assert state.attributes["color_mode"] == ColorMode.BRIGHTNESS
    assert state.attributes["supported_color_modes"] == [ColorMode.BRIGHTNESS]
    assert state.attributes["supported_features"] == 0

    set_state = STATE_OFF
    await async_trigger(hass, TEST_STATE_ENTITY_ID, set_state)
    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.state == set_state
    assert state.attributes["color_mode"] is None
    assert state.attributes["supported_color_modes"] == [ColorMode.BRIGHTNESS]
    assert state.attributes["supported_features"] == 0