async def test_invalid_values(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test that invalid values are ignored."""
    await hass.async_block_till_done()
    await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") is None
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    # turn on the light
    async_fire_mqtt_message(hass, "test_light_rgb", "on,255,215,255-255-255,rainbow")

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 255
    assert state.attributes.get("color_temp_kelvin") is None  # hs_color has priority
    assert state.attributes.get("rgb_color") == (255, 255, 255)
    assert state.attributes.get("effect") == "rainbow"

    # bad state value
    async_fire_mqtt_message(hass, "test_light_rgb", "offf")

    # state should not have changed
    state = hass.states.get("light.test")
    assert state.state == STATE_ON

    # bad brightness values
    async_fire_mqtt_message(hass, "test_light_rgb", "on,off,255-255-255")

    # brightness should not have changed
    state = hass.states.get("light.test")
    assert state.attributes.get("brightness") == 255

    # bad color values
    async_fire_mqtt_message(hass, "test_light_rgb", "on,255,a-b-c")

    # color should not have changed
    state = hass.states.get("light.test")
    assert state.attributes.get("rgb_color") == (255, 255, 255)

    # Unset color and set a valid color temperature
    async_fire_mqtt_message(hass, "test_light_rgb", "on,,215,None-None-None")
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("color_temp_kelvin") == 4651

    # bad color temp values
    async_fire_mqtt_message(hass, "test_light_rgb", "on,,off,")

    # color temp should not have changed
    state = hass.states.get("light.test")
    assert state.attributes.get("color_temp_kelvin") == 4651

    # bad effect value
    async_fire_mqtt_message(hass, "test_light_rgb", "on,255,a-b-c,white")

    # effect should not have changed
    state = hass.states.get("light.test")
    assert state.attributes.get("effect") == "rainbow"