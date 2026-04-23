async def test_temperature_action_no_template(
    hass: HomeAssistant,
    calls: list[ServiceCall],
) -> None:
    """Test setting temperature with optimistic template."""
    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.attributes.get("color_template") is None

    await _call_and_assert_action(
        hass,
        calls,
        SERVICE_TURN_ON,
        {ATTR_COLOR_TEMP_KELVIN: 2898},
        {ATTR_COLOR_TEMP_KELVIN: 2898},
        "set_temperature",
    )

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state is not None
    assert state.attributes.get("color_temp_kelvin") == 2898
    assert state.state == STATE_ON
    assert state.attributes["color_mode"] == ColorMode.COLOR_TEMP
    assert state.attributes["supported_color_modes"] == [ColorMode.COLOR_TEMP]
    assert state.attributes["supported_features"] == 0