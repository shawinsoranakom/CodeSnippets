async def test_setup_wallthermostat(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, cube: MaxCube
) -> None:
    """Test a successful setup of a wall thermostat device."""
    assert entity_registry.async_is_registered(WALL_ENTITY_ID)
    entity = entity_registry.async_get(WALL_ENTITY_ID)
    assert entity.unique_id == "AABBCCDD02"

    state = hass.states.get(WALL_ENTITY_ID)
    assert state.state == HVACMode.OFF
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "TestRoom TestWallThermostat"
    assert state.attributes.get(ATTR_HVAC_ACTION) == HVACAction.HEATING
    assert state.attributes.get(ATTR_PRESET_MODE) == PRESET_NONE
    assert state.attributes.get(ATTR_MAX_TEMP) == 29.0
    assert state.attributes.get(ATTR_MIN_TEMP) == 5.0
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 19.0
    assert state.attributes.get(ATTR_TEMPERATURE) is None