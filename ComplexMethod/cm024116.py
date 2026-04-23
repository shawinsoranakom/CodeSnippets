async def test_sending_mqtt_commands_and_optimistic(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    kelvin: int,
    payload: str,
) -> None:
    """Test the sending of command in optimistic mode."""
    fake_state = State(
        "light.test",
        "on",
        {
            "brightness": 95,
            "hs_color": [100, 100],
            "effect": "random",
            "color_temp_kelvin": 10000,
        },
    )
    mock_restore_cache(hass, (fake_state,))

    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("hs_color") == (100, 100)
    assert state.attributes.get("effect") == "random"
    assert state.attributes.get("color_temp_kelvin") is None  # hs_color has priority
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_off(hass, "light.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "off", 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_OFF

    await common.async_turn_on(hass, "light.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,,,--,-", 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON

    # Set color_temp
    await common.async_turn_on(hass, "light.test", color_temp_kelvin=kelvin)
    # Assert mireds or Kelvin as payload
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", payload, 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("color_temp_kelvin") == kelvin

    # Set full brightness
    await common.async_turn_on(hass, "light.test", brightness=255)
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,255,,--,-", 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON

    # Full brightness - no scaling of RGB values sent over MQTT
    await common.async_turn_on(hass, "light.test", rgb_color=(255, 128, 0))
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,,,255-128-0,30.118-100.0", 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (255, 128, 0)

    # Full brightness - normalization of RGB values sent over MQTT
    await common.async_turn_on(hass, "light.test", rgb_color=(128, 64, 0))
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,,,255-128-0,30.0-100.0", 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (255, 128, 0)

    # Set half brightness
    await common.async_turn_on(hass, "light.test", brightness=128)
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,128,,--,-", 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON

    # Half brightness - scaling of RGB values sent over MQTT
    await common.async_turn_on(hass, "light.test", rgb_color=(0, 255, 128))
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,,,0-128-64,150.118-100.0", 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (0, 255, 128)

    # Half brightness - normalization+scaling of RGB values sent over MQTT
    await common.async_turn_on(hass, "light.test", rgb_color=(0, 32, 16))
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "on,,,0-128-64,150.0-100.0", 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("rgb_color") == (0, 255, 128)