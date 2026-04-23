async def test_attributes(hass: HomeAssistant) -> None:
    """Test the light attributes are correct."""
    await setup_platform(hass, LIGHT_DOMAIN)

    state = hass.states.get(DEVICE_ID)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 204
    assert state.attributes.get(ATTR_RGB_COLOR) == (0, 64, 255)
    assert state.attributes.get(ATTR_COLOR_TEMP_KELVIN) is None
    assert state.attributes.get(ATTR_DEVICE_ID) == "ZB:db5b1a"
    assert not state.attributes.get("battery_low")
    assert not state.attributes.get("no_response")
    assert state.attributes.get("device_type") == "RGB Dimmer"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Living Room Lamp"
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == 0
    assert state.attributes.get(ATTR_COLOR_MODE) == ColorMode.HS
    assert state.attributes.get(ATTR_SUPPORTED_COLOR_MODES) == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
    ]