async def test_light_rgb_vs_onoff_modes(
    hass: HomeAssistant,
) -> None:
    """Test that RGB and ONOFF modes are correctly assigned based on device capabilities."""
    assert len(hass.states.async_entity_ids(LIGHT_DOMAIN)) == 2

    # Device with LED ring support should have RGB mode
    rgb_light = hass.states.get("light.device_with_led_led")
    assert rgb_light is not None
    assert rgb_light.state == STATE_ON
    assert rgb_light.attributes.get("supported_color_modes") == ["rgb"]
    assert rgb_light.attributes.get("color_mode") == "rgb"
    assert rgb_light.attributes.get("brightness") == 204
    assert rgb_light.attributes.get("rgb_color") == (0, 0, 255)

    # Device without LED ring support should have ONOFF mode
    onoff_light = hass.states.get("light.device_led_no_rgb_led")
    assert onoff_light is not None
    assert onoff_light.state == STATE_ON
    assert onoff_light.attributes.get("supported_color_modes") == ["onoff"]
    assert onoff_light.attributes.get("color_mode") == "onoff"
    assert onoff_light.attributes.get("brightness") is None
    assert onoff_light.attributes.get("rgb_color") is None