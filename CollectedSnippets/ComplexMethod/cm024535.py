async def test_attributes(hass: HomeAssistant) -> None:
    """Test the humidifier attributes are correct."""
    await setup_platform(hass, HUMIDIFIER_DOMAIN)

    state = hass.states.get(DEVICE_ID)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_ACTION] == HumidifierAction.HUMIDIFYING
    assert state.attributes[ATTR_CURRENT_HUMIDITY] == 15
    assert state.attributes[ATTR_MIN_HUMIDITY] == DEFAULT_MIN_HUMIDITY
    assert state.attributes[ATTR_MAX_HUMIDITY] == DEFAULT_MAX_HUMIDITY
    assert state.attributes[ATTR_HUMIDITY] == 40
    assert state.attributes[ATTR_AVAILABLE_MODES] == [
        MODE_OFF,
        MODE_AUTO,
        MODE_MANUAL,
    ]
    assert state.attributes[ATTR_FRIENDLY_NAME] == "ecobee"
    assert state.attributes[ATTR_DEVICE_CLASS] == HumidifierDeviceClass.HUMIDIFIER
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == HumidifierEntityFeature.MODES