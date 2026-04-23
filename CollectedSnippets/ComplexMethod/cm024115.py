async def test_state_brightness_color_effect_temp_change_via_topic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test state, bri, color, effect, color temp change."""
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("effect") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # turn on the light
    async_fire_mqtt_message(hass, "test_light_rgb", "on,255,145,255-128-64,")

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (255, 128, 64)
    assert state.attributes.get("brightness") == 255
    assert state.attributes.get("color_temp_kelvin") is None  # rgb color has priority
    assert state.attributes.get("effect") is None

    # turn on the light
    async_fire_mqtt_message(hass, "test_light_rgb", "on,255,145,None-None-None,")

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (
        246,
        244,
        255,
    )  # temp converted to color
    assert state.attributes.get("brightness") == 255
    assert state.attributes.get("color_temp_kelvin") == 6896
    assert state.attributes.get("effect") is None
    assert state.attributes.get("xy_color") == (0.317, 0.317)  # temp converted to color
    assert state.attributes.get("hs_color") == (
        251.249,
        4.253,
    )  # temp converted to color

    # make the light state unknown
    async_fire_mqtt_message(hass, "test_light_rgb", "None")

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN

    # turn the light off
    async_fire_mqtt_message(hass, "test_light_rgb", "off")

    state = hass.states.get("light.test")
    assert state.state == STATE_OFF

    # lower the brightness
    async_fire_mqtt_message(hass, "test_light_rgb", "on,100")

    light_state = hass.states.get("light.test")
    assert light_state.attributes["brightness"] == 100

    # ignore a zero brightness
    async_fire_mqtt_message(hass, "test_light_rgb", "on,0")

    light_state = hass.states.get("light.test")
    assert light_state.attributes["brightness"] == 100

    # change the color temp
    async_fire_mqtt_message(hass, "test_light_rgb", "on,,195")

    light_state = hass.states.get("light.test")
    assert light_state.attributes[light.ATTR_COLOR_TEMP_KELVIN] == 5128

    # change the color
    async_fire_mqtt_message(hass, "test_light_rgb", "on,,,41-42-43")

    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("rgb_color") == (243, 249, 255)

    # change the effect
    async_fire_mqtt_message(hass, "test_light_rgb", "on,,,41-42-43,rainbow")

    light_state = hass.states.get("light.test")
    assert light_state.attributes.get("effect") == "rainbow"