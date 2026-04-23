async def test_controlling_state_color_temp_kelvin(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the controlling of the state via topic in Kelvin mode."""
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    color_modes = [light.ColorMode.COLOR_TEMP, light.ColorMode.HS]
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes
    expected_features = (
        light.LightEntityFeature.EFFECT
        | light.LightEntityFeature.FLASH
        | light.LightEntityFeature.TRANSITION
    )
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) is expected_features
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") is None
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get("hs_color") is None
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Turn on the light
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON",'
        '"color":{"h": 44.098, "s": 2.43},'
        '"color_mode": "hs",'
        '"brightness":255,'
        '"color_temp":155,'
        '"effect":"colorloop"}',
    )

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (255, 253, 249)
    assert state.attributes.get("brightness") == 255
    assert state.attributes.get("color_temp_kelvin") is None  # rgb color has priority
    assert state.attributes.get("effect") == "colorloop"
    assert state.attributes.get("xy_color") == (0.328, 0.333)
    assert state.attributes.get("hs_color") == (44.098, 2.43)

    # Turn on the light
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON",'
        '"brightness":255,'
        '"color":null,'
        '"color_mode":"color_temp",'
        '"color_temp":6451,'  # Kelvin
        '"effect":"colorloop"}',
    )

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (
        255,
        253,
        249,
    )  # temp converted to color
    assert state.attributes.get("brightness") == 255
    assert state.attributes.get("color_temp_kelvin") == 6451
    assert state.attributes.get("effect") == "colorloop"
    assert state.attributes.get("xy_color") == (0.328, 0.333)  # temp converted to color
    assert state.attributes.get("hs_color") == (44.098, 2.43)