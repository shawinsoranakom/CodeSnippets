async def test_sending_mqtt_commands_and_optimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the sending of command in optimistic mode."""
    color_modes = ["color_temp", "hs", "rgb", "rgbw", "rgbww", "xy"]
    fake_state = State(
        "light.test",
        "on",
        {
            "brightness": 95,
            "hs_color": [100, 100],
            "effect": "random",
            "color_temp_kelvin": 100000,
            "color_mode": "hs",
        },
    )
    mock_restore_cache(hass, (fake_state,))

    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 95
    assert state.attributes.get("hs_color") == (100, 100)
    assert state.attributes.get("effect") == "random"
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "hs"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    await common.async_turn_on(hass, "light.test", effect="colorloop")
    mqtt_mock.async_publish.assert_has_calls(
        [
            call("test_light_rgb/set", "on", 2, False),
            call("test_light_rgb/effect/set", "colorloop", 2, False),
        ],
        any_order=True,
    )
    assert mqtt_mock.async_publish.call_count == 2
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("effect") == "colorloop"
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "hs"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    await common.async_turn_off(hass, "light.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", "off", 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_OFF
    assert state.attributes.get(light.ATTR_COLOR_MODE) is None
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    await common.async_turn_on(
        hass, "light.test", brightness=10, rgb_color=(80, 40, 20)
    )
    mqtt_mock.async_publish.assert_has_calls(
        [
            call("test_light_rgb/set", "on", 2, False),
            call("test_light_rgb/brightness/set", "10", 2, False),
            call("test_light_rgb/rgb/set", "80,40,20", 2, False),
        ],
        any_order=True,
    )
    assert mqtt_mock.async_publish.call_count == 3
    mqtt_mock.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 10
    assert state.attributes.get("rgb_color") == (80, 40, 20)
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "rgb"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    await common.async_turn_on(
        hass, "light.test", brightness=20, rgbw_color=(80, 40, 20, 10)
    )
    mqtt_mock.async_publish.assert_has_calls(
        [
            call("test_light_rgb/set", "on", 2, False),
            call("test_light_rgb/brightness/set", "20", 2, False),
            call("test_light_rgb/rgbw/set", "80,40,20,10", 2, False),
        ],
        any_order=True,
    )
    assert mqtt_mock.async_publish.call_count == 3
    mqtt_mock.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 20
    assert state.attributes.get("rgbw_color") == (80, 40, 20, 10)
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "rgbw"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    await common.async_turn_on(
        hass, "light.test", brightness=40, rgbww_color=(80, 40, 20, 10, 8)
    )
    mqtt_mock.async_publish.assert_has_calls(
        [
            call("test_light_rgb/set", "on", 2, False),
            call("test_light_rgb/brightness/set", "40", 2, False),
            call("test_light_rgb/rgbww/set", "80,40,20,10,8", 2, False),
        ],
        any_order=True,
    )
    assert mqtt_mock.async_publish.call_count == 3
    mqtt_mock.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 40
    assert state.attributes.get("rgbww_color") == (80, 40, 20, 10, 8)
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "rgbww"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    await common.async_turn_on(hass, "light.test", brightness=50, hs_color=(359, 78))
    mqtt_mock.async_publish.assert_has_calls(
        [
            call("test_light_rgb/set", "on", 2, False),
            call("test_light_rgb/brightness/set", "50", 2, False),
            call("test_light_rgb/hs/set", "359.0,78.0", 2, False),
        ],
        any_order=True,
    )
    assert mqtt_mock.async_publish.call_count == 3
    mqtt_mock.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 50
    assert state.attributes.get("hs_color") == (359.0, 78.0)
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "hs"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    await common.async_turn_on(hass, "light.test", brightness=60, xy_color=(0.2, 0.3))
    mqtt_mock.async_publish.assert_has_calls(
        [
            call("test_light_rgb/set", "on", 2, False),
            call("test_light_rgb/brightness/set", "60", 2, False),
            call("test_light_rgb/xy/set", "0.2,0.3", 2, False),
        ],
        any_order=True,
    )
    assert mqtt_mock.async_publish.call_count == 3
    mqtt_mock.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 60
    assert state.attributes.get("xy_color") == (0.2, 0.3)
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "xy"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes

    await common.async_turn_on(hass, "light.test", color_temp_kelvin=8000)
    mqtt_mock.async_publish.assert_has_calls(
        [
            call("test_light_rgb/color_temp/set", "125", 2, False),
        ],
        any_order=True,
    )
    assert mqtt_mock.async_publish.call_count == 2
    mqtt_mock.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("brightness") == 60
    assert state.attributes.get("color_temp_kelvin") == 8000
    assert state.attributes.get(light.ATTR_COLOR_MODE) == "color_temp"
    assert state.attributes.get(light.ATTR_SUPPORTED_COLOR_MODES) == color_modes