async def test_sending_mqtt_commands_and_optimistic(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the sending of command in optimistic mode for a light supporting color mode."""
    supported_color_modes = ["color_temp", "hs", "rgb", "rgbw", "rgbww", "white", "xy"]
    fake_state = State(
        "light.test",
        "on",
        {
            "brightness": 95,
            "color_temp_kelvin": 10000,
            "color_mode": "rgb",
            "effect": "random",
            "hs_color": [100, 100],
        },
    )
    mock_restore_cache(hass, (fake_state,))

    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    expected_features = (
        light.LightEntityFeature.EFFECT
        | light.LightEntityFeature.FLASH
        | light.LightEntityFeature.TRANSITION
    )
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) is expected_features
    assert state.attributes.get("brightness") == 95
    assert state.attributes.get("color_mode") == "rgb"
    assert state.attributes.get("color_temp_kelvin") is None
    assert state.attributes.get("effect") == "random"
    assert state.attributes.get("hs_color") is None
    assert state.attributes.get("rgb_color") is None
    assert state.attributes.get("rgbw_color") is None
    assert state.attributes.get("rgbww_color") is None
    assert state.attributes.get("supported_color_modes") == supported_color_modes
    assert state.attributes.get("white") is None
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get(ATTR_ASSUMED_STATE)

    # Turn the light on
    await common.async_turn_on(hass, "light.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", '{"state":"ON"}', 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON

    # Turn the light on with color temperature
    await common.async_turn_on(hass, "light.test", color_temp_kelvin=11111)
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set",
        JsonValidator('{"state":"ON","color_temp":90}'),
        2,
        False,
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON

    # Turn the light off
    await common.async_turn_off(hass, "light.test")
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", '{"state":"OFF"}', 2, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_OFF

    # Set hs color
    await common.async_turn_on(hass, "light.test", brightness=75, hs_color=(359, 78))
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes["brightness"] == 75
    assert state.attributes["color_mode"] == "hs"
    assert state.attributes["hs_color"] == (359, 78)
    assert state.attributes["rgb_color"] == (255, 56, 59)
    assert state.attributes["xy_color"] == (0.654, 0.301)
    assert state.attributes["rgbw_color"] is None
    assert state.attributes["rgbww_color"] is None
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set",
        JsonValidator(
            '{"state": "ON", "color": {"h": 359.0, "s": 78.0}, "brightness": 75}'
        ),
        2,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Set rgb color
    await common.async_turn_on(hass, "light.test", rgb_color=(255, 128, 0))
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes["brightness"] == 75
    assert state.attributes["color_mode"] == "rgb"
    assert state.attributes["hs_color"] == (30.118, 100.0)
    assert state.attributes["rgb_color"] == (255, 128, 0)
    assert state.attributes["xy_color"] == (0.611, 0.375)
    assert state.attributes["rgbw_color"] is None
    assert state.attributes["rgbww_color"] is None
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set",
        JsonValidator('{"state": "ON", "color": {"r": 255, "g": 128, "b": 0} }'),
        2,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Set rgbw color
    await common.async_turn_on(hass, "light.test", rgbw_color=(255, 128, 0, 123))
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes["brightness"] == 75
    assert state.attributes["color_mode"] == "rgbw"
    assert state.attributes["rgbw_color"] == (255, 128, 0, 123)
    assert state.attributes["hs_color"] == (30.0, 67.451)
    assert state.attributes["rgb_color"] == (255, 169, 83)
    assert state.attributes["rgbww_color"] is None
    assert state.attributes["xy_color"] == (0.526, 0.393)
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set",
        JsonValidator(
            '{"state": "ON", "color": {"r": 255, "g": 128, "b": 0, "w": 123} }'
        ),
        2,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Set rgbww color
    await common.async_turn_on(hass, "light.test", rgbww_color=(255, 128, 0, 45, 32))
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes["brightness"] == 75
    assert state.attributes["color_mode"] == "rgbww"
    assert state.attributes["rgbww_color"] == (255, 128, 0, 45, 32)
    assert state.attributes["hs_color"] == (29.872, 92.157)
    assert state.attributes["rgb_color"] == (255, 137, 20)
    assert state.attributes["rgbw_color"] is None
    assert state.attributes["xy_color"] == (0.596, 0.382)
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set",
        JsonValidator(
            '{"state": "ON", "color": {"r": 255, "g": 128, "b": 0, "c": 45, "w": 32} }'
        ),
        2,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Set xy color
    await common.async_turn_on(
        hass, "light.test", brightness=50, xy_color=(0.123, 0.223)
    )
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes["brightness"] == 50
    assert state.attributes["color_mode"] == "xy"
    assert state.attributes["hs_color"] == (196.471, 100.0)
    assert state.attributes["rgb_color"] == (0, 185, 255)
    assert state.attributes["xy_color"] == (0.123, 0.223)
    assert state.attributes["rgbw_color"] is None
    assert state.attributes["rgbww_color"] is None
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set",
        JsonValidator(
            '{"state": "ON", "color": {"x": 0.123, "y": 0.223}, "brightness": 50}'
        ),
        2,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Set to white
    await common.async_turn_on(hass, "light.test", white=75)
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes["brightness"] == 75
    assert state.attributes["color_mode"] == "white"
    assert state.attributes["hs_color"] is None
    assert state.attributes["rgb_color"] is None
    assert state.attributes["xy_color"] is None
    assert state.attributes["rgbw_color"] is None
    assert state.attributes["rgbww_color"] is None
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set",
        JsonValidator('{"state": "ON", "white": 75}'),
        2,
        False,
    )
    mqtt_mock.async_publish.reset_mock()

    # Set to white, brightness also present in turn_on
    await common.async_turn_on(hass, "light.test", brightness=60, white=80)
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes["brightness"] == 60
    assert state.attributes["color_mode"] == "white"
    assert state.attributes["hs_color"] is None
    assert state.attributes["rgb_color"] is None
    assert state.attributes["xy_color"] is None
    assert state.attributes["rgbw_color"] is None
    assert state.attributes["rgbww_color"] is None
    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set",
        JsonValidator('{"state": "ON", "white": 60}'),
        2,
        False,
    )
    mqtt_mock.async_publish.reset_mock()