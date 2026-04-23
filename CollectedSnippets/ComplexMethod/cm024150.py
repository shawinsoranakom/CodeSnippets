async def test_effect(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test for effect being sent when included."""
    mqtt_mock = await mqtt_mock_entry()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    expected_features = (
        light.LightEntityFeature.EFFECT
        | light.LightEntityFeature.FLASH
        | light.LightEntityFeature.TRANSITION
    )
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) is expected_features

    await common.async_turn_on(hass, "light.test")

    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set", JsonValidator('{"state": "ON"}'), 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("effect") is None

    await common.async_turn_on(hass, "light.test", effect="rainbow")

    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set",
        JsonValidator('{"state": "ON", "effect": "rainbow"}'),
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("effect") == "rainbow"

    await common.async_turn_on(hass, "light.test", effect="colorloop")

    mqtt_mock.async_publish.assert_called_once_with(
        "test_light_rgb/set",
        JsonValidator('{"state": "ON", "effect": "colorloop"}'),
        0,
        False,
    )
    mqtt_mock.async_publish.reset_mock()
    state = hass.states.get("light.test")
    assert state.state == STATE_ON
    assert state.attributes.get("effect") == "colorloop"