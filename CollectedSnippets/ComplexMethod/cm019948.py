async def test_filter_color_modes_missing_attributes(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test warning on missing attribute when filtering for color mode."""
    color_mode = light.ColorMode.COLOR_TEMP
    hass.states.async_set("light.entity", "off", {})
    expected_log = (
        "Color mode color_temp specified "
        "but attribute color_temp_kelvin missing for: light.entity"
    )
    expected_fallback_log = "using color_temp (mireds) as fallback"

    turn_on_calls = async_mock_service(hass, "light", "turn_on")

    all_colors = {
        **VALID_COLOR_TEMP_KELVIN,
        **VALID_HS_COLOR,
        **VALID_RGB_COLOR,
        **VALID_RGBW_COLOR,
        **VALID_RGBWW_COLOR,
        **VALID_XY_COLOR,
        **VALID_BRIGHTNESS,
    }

    # Test missing `color_temp_kelvin` attribute
    stored_attributes = {**all_colors}
    stored_attributes.pop("color_temp_kelvin")
    caplog.clear()
    await async_reproduce_state(
        hass,
        [State("light.entity", "on", {**stored_attributes, "color_mode": color_mode})],
    )
    assert len(turn_on_calls) == 0
    assert expected_log in caplog.text
    assert expected_fallback_log not in caplog.text

    # Test with correct `color_temp_kelvin` attribute
    expected = {"brightness": 180, "color_temp_kelvin": 4200}
    caplog.clear()
    turn_on_calls.clear()
    await async_reproduce_state(
        hass,
        [State("light.entity", "on", {**all_colors, "color_mode": color_mode})],
    )
    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].domain == "light"
    assert dict(turn_on_calls[0].data) == {"entity_id": "light.entity", **expected}
    assert expected_log not in caplog.text
    assert expected_fallback_log not in caplog.text