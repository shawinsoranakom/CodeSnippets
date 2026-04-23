async def test_supported_features(hass: HomeAssistant) -> None:
    """Test vacuum supported features."""
    state = hass.states.get(ENTITY_VACUUM_COMPLETE)
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == 32700
    assert state.attributes.get(ATTR_FAN_SPEED) == "medium"
    assert state.attributes.get(ATTR_FAN_SPEED_LIST) == FAN_SPEEDS
    assert state.state == VacuumActivity.DOCKED

    state = hass.states.get(ENTITY_VACUUM_MOST)
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == 12348
    assert state.attributes.get(ATTR_FAN_SPEED) == "medium"
    assert state.attributes.get(ATTR_FAN_SPEED_LIST) == FAN_SPEEDS
    assert state.state == VacuumActivity.DOCKED

    state = hass.states.get(ENTITY_VACUUM_BASIC)
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == 12296
    assert state.attributes.get(ATTR_FAN_SPEED) is None
    assert state.attributes.get(ATTR_FAN_SPEED_LIST) is None
    assert state.state == VacuumActivity.DOCKED

    state = hass.states.get(ENTITY_VACUUM_MINIMAL)
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == 3
    assert state.attributes.get(ATTR_FAN_SPEED) is None
    assert state.attributes.get(ATTR_FAN_SPEED_LIST) is None
    assert state.state == VacuumActivity.DOCKED

    state = hass.states.get(ENTITY_VACUUM_NONE)
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == 0
    assert state.attributes.get(ATTR_FAN_SPEED) is None
    assert state.attributes.get(ATTR_FAN_SPEED_LIST) is None
    assert state.state == VacuumActivity.DOCKED