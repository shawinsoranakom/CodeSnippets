def test_setup_params(hass: HomeAssistant) -> None:
    """Test the initial parameters."""
    state = hass.states.get(ENTITY_CLIMATE)
    assert state.state == HVACMode.COOL
    assert state.attributes.get(ATTR_TEMPERATURE) == 21
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 22
    assert state.attributes.get(ATTR_FAN_MODE) == "on_high"
    assert state.attributes.get(ATTR_HUMIDITY) == 67.4
    assert state.attributes.get(ATTR_CURRENT_HUMIDITY) == 54.2
    assert state.attributes.get(ATTR_SWING_MODE) == "off"
    assert state.attributes.get(ATTR_HVAC_MODES) == [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.AUTO,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]