async def test_state_templates_ignore_missing_values(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
) -> None:
    """Test that rendering of MQTT value template ignores missing values."""
    await mqtt_mock_entry()

    # turn on the light
    async_fire_mqtt_message(hass, "test-topic", '{"state": "on"}')
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") is None

    # update brightness and color temperature (with no state)
    async_fire_mqtt_message(
        hass, "test-topic", '{"brightness": 255, "color_temp": 145}'
    )
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

    # update color
    async_fire_mqtt_message(
        hass, "test-topic", '{"color": {"red": 255, "green": 128, "blue": 64}}'
    )
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (255, 128, 64)
    assert state.attributes.get("brightness") == 255
    assert state.attributes.get("color_temp_kelvin") is None  # rgb color has priority
    assert state.attributes.get("effect") is None

    # update brightness
    async_fire_mqtt_message(hass, "test-topic", '{"brightness": 128}')
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (255, 128, 64)
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("color_temp_kelvin") is None  # rgb color has priority
    assert state.attributes.get("effect") is None

    # update effect
    async_fire_mqtt_message(hass, "test-topic", '{"effect": "rainbow"}')
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (255, 128, 64)
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("color_temp_kelvin") is None  # rgb color has priority
    assert state.attributes.get("effect") == "rainbow"

    # invalid effect
    async_fire_mqtt_message(hass, "test-topic", '{"effect": "invalid"}')
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (255, 128, 64)
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("color_temp_kelvin") is None  # rgb color has priority
    assert state.attributes.get("effect") == "rainbow"

    # turn off the light
    async_fire_mqtt_message(hass, "test-topic", '{"state": "off"}')
    state = hass.states.get("light.test")
    assert state.state == STATE_OFF
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("brightness") is None
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") is None