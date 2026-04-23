async def test_sending_mqtt_commands_non_optimistic_brightness_template(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the sending of command in optimistic mode."""
    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get("brightness")
    assert not state.attributes.get("hs_color")
    assert not state.attributes.get("effect")
    assert not state.attributes.get("color_temp")
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_off(hass, "light.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "off", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN

    await common.async_turn_on(hass, "light.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,,,--,-", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN

    # Set color_temp
    await common.async_turn_on(hass, "light.test", color_temp_kelvin=14285)
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,,70,--,-", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get("color_temp")

    # Set full brightness
    await common.async_turn_on(hass, "light.test", brightness=255)
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,255,,--,-", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get("brightness")

    # Full brightness - no scaling of RGB values sent over MQTT
    await common.async_turn_on(hass, "light.test", rgb_color=(255, 128, 0))
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,,,255-128-0,30.118-100.0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert not state.attributes.get("rgb_color")

    # Full brightness - normalization of RGB values sent over MQTT
    await common.async_turn_on(hass, "light.test", rgb_color=(128, 64, 0))
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,,,255-128-0,30.0-100.0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()

    # Set half brightness
    await common.async_turn_on(hass, "light.test", brightness=128)
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,128,,--,-", 0, False
    )
    mqtt_mock.async_publish.reset_mock()

    # Half brightness - no scaling of RGB values sent over MQTT
    await common.async_turn_on(hass, "light.test", rgb_color=(0, 255, 128))
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,,,0-255-128,150.118-100.0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")

    # Half brightness - normalization but no scaling of RGB values sent over MQTT
    await common.async_turn_on(hass, "light.test", rgb_color=(0, 32, 16))
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,,,0-255-128,150.0-100.0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")