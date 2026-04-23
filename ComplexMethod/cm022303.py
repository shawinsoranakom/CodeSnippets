async def test_lights(
    hass: HomeAssistant, mock_bridge_v2: Mock, v2_resources_test_data: JsonArrayType
) -> None:
    """Test if all v2 lights get created with correct features."""
    await mock_bridge_v2.api.load_test_data(v2_resources_test_data)

    await setup_platform(hass, mock_bridge_v2, Platform.LIGHT)
    # there shouldn't have been any requests at this point
    assert len(mock_bridge_v2.mock_requests) == 0
    # 8 entities should be created from test data
    assert len(hass.states.async_all()) == 8

    # test light which supports color and color temperature
    light_1 = hass.states.get("light.hue_light_with_color_and_color_temperature_1")
    assert light_1 is not None
    assert (
        light_1.attributes["friendly_name"]
        == "Hue light with color and color temperature 1"
    )
    assert light_1.state == "on"
    assert light_1.attributes["brightness"] == int(46.85 / 100 * 255)
    assert light_1.attributes["mode"] == "normal"
    assert light_1.attributes["color_mode"] == ColorMode.XY
    assert set(light_1.attributes["supported_color_modes"]) == {
        ColorMode.COLOR_TEMP,
        ColorMode.XY,
    }
    assert light_1.attributes["xy_color"] == (0.5614, 0.4058)
    assert light_1.attributes["max_color_temp_kelvin"] == 6535
    assert light_1.attributes["min_color_temp_kelvin"] == 2000
    assert light_1.attributes["dynamics"] == "dynamic_palette"
    assert light_1.attributes["effect_list"] == ["off", "candle", "fire"]
    assert light_1.attributes["effect"] == "off"

    # test light which supports color temperature only
    light_2 = hass.states.get("light.hue_light_with_color_temperature_only")
    assert light_2 is not None
    assert (
        light_2.attributes["friendly_name"] == "Hue light with color temperature only"
    )
    assert light_2.state == "off"
    assert light_2.attributes["mode"] == "normal"
    assert light_2.attributes["supported_color_modes"] == [ColorMode.COLOR_TEMP]
    assert light_2.attributes["max_color_temp_kelvin"] == 6535
    assert light_2.attributes["min_color_temp_kelvin"] == 2202
    assert light_2.attributes["dynamics"] == "none"
    assert light_2.attributes["effect_list"] == ["off", "candle", "sunrise"]

    # test light which supports color only
    light_3 = hass.states.get("light.hue_light_with_color_only")
    assert light_3 is not None
    assert light_3.attributes["friendly_name"] == "Hue light with color only"
    assert light_3.state == "on"
    assert light_3.attributes["brightness"] == 128
    assert light_3.attributes["mode"] == "normal"
    assert light_3.attributes["supported_color_modes"] == [ColorMode.XY]
    assert light_3.attributes["color_mode"] == ColorMode.XY
    assert light_3.attributes["dynamics"] == "dynamic_palette"

    # test light which supports on/off only
    light_4 = hass.states.get("light.hue_on_off_light")
    assert light_4 is not None
    assert light_4.attributes["friendly_name"] == "Hue on/off light"
    assert light_4.state == "off"
    assert light_4.attributes["mode"] == "normal"
    assert light_4.attributes["supported_color_modes"] == [ColorMode.ONOFF]