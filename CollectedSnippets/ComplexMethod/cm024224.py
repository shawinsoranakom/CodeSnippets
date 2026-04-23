async def test_brightness_from_rgb_controlling_scale(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the brightness controlling scale."""
    mqtt_mock = await mqtt_mock_entry()
    await hass.async_block_till_done()

    state = hass.states.get("light.test")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("brightness") is None
    assert not state.attributes.get(ATTR_ASSUMED_STATE)

    async_fire_mqtt_message(hass, "test_scale_rgb/status", "on")
    async_fire_mqtt_message(hass, "test_scale_rgb/rgb/status", "255,0,0")

    state = hass.states.get("light.test")
    assert state.attributes.get("brightness") == 255

    async_fire_mqtt_message(hass, "test_scale_rgb/rgb/status", "128,64,32")

    state = hass.states.get("light.test")
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("rgb_color") == (255, 128, 64)

    # Test zero rgb is ignored
    async_fire_mqtt_message(hass, "test_scale_rgb/rgb/status", "0,0,0")
    state = hass.states.get("light.test")
    assert state.attributes.get("brightness") == 128
    assert state.attributes.get("rgb_color") == (255, 128, 64)

    mqtt_mock.async_publish.reset_mock()
    await common.async_turn_on(hass, "light.test", brightness=191)
    await hass.async_block_till_done()

    mqtt_mock.async_publish.assert_has_calls(
        [
            call("test_scale_rgb/set", "on", 0, False),
            call("test_scale_rgb/rgb/set", "191,95,47", 0, False),
        ],
        any_order=True,
    )
    async_fire_mqtt_message(hass, "test_scale_rgb/rgb/status", "191,95,47")
    await hass.async_block_till_done()

    state = hass.states.get("light.test")
    assert state.attributes.get("brightness") == 191
    assert state.attributes.get("rgb_color") == (255, 127, 63)