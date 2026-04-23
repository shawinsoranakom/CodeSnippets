async def test_light_state_update_via_websocket(
    hass: HomeAssistant,
    mock_websocket_message: WebsocketMessageMock,
) -> None:
    """Test state update via websocket."""
    light_entity = hass.states.get("light.device_with_led_led")
    assert light_entity is not None
    assert light_entity.state == STATE_ON
    assert light_entity.attributes["rgb_color"] == (0, 0, 255)
    updated_device = deepcopy(DEVICE_WITH_LED)
    updated_device["led_override"] = "off"
    updated_device["led_override_color"] = "#ff0000"
    updated_device["led_override_color_brightness"] = 100

    mock_websocket_message(message=MessageKey.DEVICE, data=[updated_device])
    await hass.async_block_till_done()

    light_entity = hass.states.get("light.device_with_led_led")
    assert light_entity is not None
    assert light_entity.state == STATE_OFF
    assert light_entity.attributes.get("rgb_color") is None
    assert light_entity.attributes.get("brightness") is None