async def test_config_fan_mode_register(hass: HomeAssistant, mock_modbus) -> None:
    """Run configuration test for Fan mode register."""
    state = hass.states.get(ENTITY_ID)
    assert FAN_ON in state.attributes[ATTR_FAN_MODES]
    assert FAN_OFF in state.attributes[ATTR_FAN_MODES]
    assert FAN_AUTO in state.attributes[ATTR_FAN_MODES]
    assert FAN_LOW in state.attributes[ATTR_FAN_MODES]
    assert FAN_MEDIUM in state.attributes[ATTR_FAN_MODES]
    assert FAN_HIGH in state.attributes[ATTR_FAN_MODES]
    assert FAN_TOP not in state.attributes[ATTR_FAN_MODES]
    assert FAN_MIDDLE not in state.attributes[ATTR_FAN_MODES]
    assert FAN_DIFFUSE not in state.attributes[ATTR_FAN_MODES]
    assert FAN_FOCUS not in state.attributes[ATTR_FAN_MODES]