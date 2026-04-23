async def test_light_onoff_mode_only(
    hass: HomeAssistant,
) -> None:
    """Test light with ONOFF mode only (no LED ring support)."""
    assert len(hass.states.async_entity_ids(LIGHT_DOMAIN)) == 1

    light_entity = hass.states.get("light.device_led_no_rgb_led")
    assert light_entity is not None
    assert light_entity.state == STATE_ON
    # Device without LED ring support should not expose brightness or RGB
    assert light_entity.attributes.get("brightness") is None
    assert light_entity.attributes.get("rgb_color") is None
    assert light_entity.attributes.get("supported_color_modes") == ["onoff"]
    assert light_entity.attributes.get("color_mode") == "onoff"