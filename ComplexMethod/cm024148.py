async def test_controlling_state_via_topic(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the controlling of the state via topic for a light supporting color mode."""
    supported_color_modes = ["color_temp", "hs", "rgb", "rgbw", "rgbww", "white", "xy"]
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    expected_features = (
        light.LightEntityFeature.EFFECT
        | light.LightEntityFeature.FLASH
        | light.LightEntityFeature.TRANSITION
    )
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) is expected_features
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_mode") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") is None
    assert state.attributes.get("hs_color") is None
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("rgbw_color") is None
    assert state.attributes.get("rgbww_color") is None
    assert state.attributes.get("supported_color_modes") == supported_color_modes
    assert state.attributes.get("xy_color") is None
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # Turn on the light, rgbww mode, additional values in the update
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON",'
        '"color_mode":"rgbww",'
        '"color":{"r":255,"g":128,"b":64, "c": 32, "w": 16, "x": 1, "y": 1},'
        '"brightness":255,'
        '"color_temp":155,'
        '"effect":"colorloop"}',
    )

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 255
    assert state.attributes.get("color_mode") == "rgbww"
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") == "colorloop"
    assert state.attributes.get("hs_color") == (20.552, 70.98)
    assert state.attributes.get("rgb_color") == (255, 136, 74)
    assert state.attributes.get("rgbw_color") is None
    assert state.attributes.get("rgbww_color") == (255, 128, 64, 32, 16)
    assert state.attributes.get("xy_color") == (0.571, 0.361)

    # Light turned off
    async_fire_mqtt_message(hass, "test_light_rgb", '{"state":"OFF"}')
    state = hass.states.get("light.test")
    assert state.state == STATE_OFF

    # Light turned on, brightness 100
    async_fire_mqtt_message(hass, "test_light_rgb", '{"state":"ON", "brightness":100}')
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 100

    # Zero brightness value is ignored
    async_fire_mqtt_message(hass, "test_light_rgb", '{"state":"ON", "brightness":0}')
    state = hass.states.get("light.test")
    assert state.attributes["brightness"] == 100

    # RGB color
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color_mode":"rgb", "color":{"r":64,"g":128,"b":255}}',
    )
    state = hass.states.get("light.test")
    assert state.attributes.get("color_mode") == "rgb"
    assert state.attributes.get("rgb_color") == (64, 128, 255)

    # RGBW color
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color_mode":"rgbw", "color":{"r":64,"g":128,"b":255,"w":32}}',
    )
    state = hass.states.get("light.test")
    assert state.attributes.get("color_mode") == "rgbw"
    assert state.attributes.get("rgbw_color") == (64, 128, 255, 32)

    # XY color
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color_mode":"xy", "color":{"x":0.135,"y":0.235}}',
    )
    state = hass.states.get("light.test")
    assert state.attributes.get("color_mode") == "xy"
    assert state.attributes.get("xy_color") == (0.135, 0.235)

    # HS color
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color_mode":"hs", "color":{"h":180,"s":50}}',
    )
    state = hass.states.get("light.test")
    assert state.attributes.get("color_mode") == "hs"
    assert state.attributes.get("hs_color") == (180.0, 50.0)

    # Color temp
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color_mode":"color_temp", "color_temp":155}',
    )
    state = hass.states.get("light.test")
    assert state.attributes.get("color_mode") == "color_temp"
    assert state.attributes.get("color_temp_kelvin") == 6451

    # White
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color_mode":"white", "brightness":123}',
    )
    state = hass.states.get("light.test")
    assert state.attributes.get("color_mode") == "white"
    assert state.attributes.get("brightness") == 123

    # Effect
    async_fire_mqtt_message(
        hass, "test_light_rgb", '{"state":"ON", "effect":"other_effect"}'
    )
    state = hass.states.get("light.test")
    assert state.attributes.get("effect") == "other_effect"

    # Invalid color mode
    async_fire_mqtt_message(
        hass, "test_light_rgb", '{"state":"ON", "color_mode":"col_temp"}'
    )
    assert "Invalid color mode 'col_temp' received" in caplog.text
    caplog.clear()

    # Incomplete color
    async_fire_mqtt_message(
        hass, "test_light_rgb", '{"state":"ON", "color_mode":"rgb"}'
    )
    assert (
        "Invalid or incomplete color value '{'state': 'ON', 'color_mode': 'rgb'}' received"
        in caplog.text
    )
    caplog.clear()

    # Invalid color
    async_fire_mqtt_message(
        hass,
        "test_light_rgb",
        '{"state":"ON", "color_mode":"rgb", "color":{"r":64,"g":128,"b":"cow"}}',
    )
    assert (
        "Invalid or incomplete color value '{'state': 'ON', 'color_mode': 'rgb', 'color': {'r': 64, 'g': 128, 'b': 'cow'}}' received"
        in caplog.text
    )