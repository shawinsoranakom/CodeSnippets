async def test_all_colors_mode_no_template(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test setting color and color temperature with optimistic template."""
    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.attributes.get("hs_color") is None

    await _call_and_assert_action(
        hass,
        calls,
        SERVICE_TURN_ON,
        {ATTR_HS_COLOR: (40, 50)},
        {"h": 40, "s": 50},
        "set_hs",
    )

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.attributes["color_mode"] == ColorMode.HS
    assert state.attributes["color_temp_kelvin"] is None
    assert state.attributes["hs_color"] == (40, 50)
    assert state.attributes["supported_color_modes"] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
        ColorMode.RGB,
        ColorMode.RGBW,
        ColorMode.RGBWW,
    ]
    assert state.attributes["supported_features"] == 0

    await _call_and_assert_action(
        hass,
        calls,
        SERVICE_TURN_ON,
        {ATTR_COLOR_TEMP_KELVIN: 8130},
        {ATTR_COLOR_TEMP_KELVIN: 8130, "color_temp": 123},
        "set_temperature",
    )

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.attributes["color_mode"] == ColorMode.COLOR_TEMP
    assert state.attributes["color_temp_kelvin"] == 8130
    assert "hs_color" in state.attributes  # Color temp represented as hs_color
    assert state.attributes["supported_color_modes"] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
        ColorMode.RGB,
        ColorMode.RGBW,
        ColorMode.RGBWW,
    ]
    assert state.attributes["supported_features"] == 0

    await _call_and_assert_action(
        hass,
        calls,
        SERVICE_TURN_ON,
        {ATTR_RGB_COLOR: (160, 78, 192)},
        {"r": 160, "g": 78, "b": 192},
        "set_rgb",
    )

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.attributes["color_mode"] == ColorMode.RGB
    assert state.attributes["color_temp_kelvin"] is None
    assert state.attributes["rgb_color"] == (160, 78, 192)
    assert state.attributes["supported_color_modes"] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
        ColorMode.RGB,
        ColorMode.RGBW,
        ColorMode.RGBWW,
    ]
    assert state.attributes["supported_features"] == 0

    await _call_and_assert_action(
        hass,
        calls,
        SERVICE_TURN_ON,
        {ATTR_RGBW_COLOR: (160, 78, 192, 25)},
        {"r": 160, "g": 78, "b": 192, "w": 25},
        "set_rgbw",
    )

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.attributes["color_mode"] == ColorMode.RGBW
    assert state.attributes["color_temp_kelvin"] is None
    assert state.attributes["rgbw_color"] == (160, 78, 192, 25)
    assert state.attributes["supported_color_modes"] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
        ColorMode.RGB,
        ColorMode.RGBW,
        ColorMode.RGBWW,
    ]
    assert state.attributes["supported_features"] == 0

    await _call_and_assert_action(
        hass,
        calls,
        SERVICE_TURN_ON,
        {ATTR_RGBWW_COLOR: (160, 78, 192, 25, 55)},
        {"r": 160, "g": 78, "b": 192, "cw": 25, "ww": 55},
        "set_rgbww",
    )

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.attributes["color_mode"] == ColorMode.RGBWW
    assert state.attributes["color_temp_kelvin"] is None
    assert state.attributes["rgbww_color"] == (160, 78, 192, 25, 55)
    assert state.attributes["supported_color_modes"] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
        ColorMode.RGB,
        ColorMode.RGBW,
        ColorMode.RGBWW,
    ]
    assert state.attributes["supported_features"] == 0

    await _call_and_assert_action(
        hass,
        calls,
        SERVICE_TURN_ON,
        {ATTR_HS_COLOR: (10, 20)},
        {"h": 10, "s": 20},
        "set_hs",
    )

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.attributes["color_mode"] == ColorMode.HS
    assert state.attributes["color_temp_kelvin"] is None
    assert state.attributes["hs_color"] == (10, 20)
    assert state.attributes["supported_color_modes"] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
        ColorMode.RGB,
        ColorMode.RGBW,
        ColorMode.RGBWW,
    ]
    assert state.attributes["supported_features"] == 0

    await _call_and_assert_action(
        hass,
        calls,
        SERVICE_TURN_ON,
        {ATTR_COLOR_TEMP_KELVIN: 4273},
        {ATTR_COLOR_TEMP_KELVIN: 4273, "color_temp": 234},
        "set_temperature",
    )

    state = hass.states.get(TEST_LIGHT.entity_id)
    assert state.attributes["color_mode"] == ColorMode.COLOR_TEMP
    assert state.attributes["color_temp_kelvin"] == 4273
    assert "hs_color" in state.attributes  # Color temp represented as hs_color
    assert state.attributes["supported_color_modes"] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
        ColorMode.RGB,
        ColorMode.RGBW,
        ColorMode.RGBWW,
    ]
    assert state.attributes["supported_features"] == 0