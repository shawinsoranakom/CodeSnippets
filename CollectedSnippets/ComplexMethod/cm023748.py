async def test_setup_thermostat(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, cube: MaxCube
) -> None:
    """Test a successful setup of a thermostat device."""
    assert entity_registry.async_is_registered(ENTITY_ID)
    entity = entity_registry.async_get(ENTITY_ID)
    assert entity.unique_id == "AABBCCDD01"

    state = hass.states.get(ENTITY_ID)
    assert state.state == HVACMode.AUTO
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "TestRoom TestThermostat"
    assert state.attributes.get(ATTR_HVAC_ACTION) == HVACAction.HEATING
    assert state.attributes.get(ATTR_HVAC_MODES) == [
        HVACMode.OFF,
        HVACMode.AUTO,
        HVACMode.HEAT,
    ]
    assert state.attributes.get(ATTR_PRESET_MODES) == [
        PRESET_NONE,
        PRESET_BOOST,
        PRESET_COMFORT,
        PRESET_ECO,
        PRESET_AWAY,
        PRESET_ON,
    ]
    assert state.attributes.get(ATTR_PRESET_MODE) == PRESET_NONE
    assert (
        state.attributes.get(ATTR_SUPPORTED_FEATURES)
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    assert state.attributes.get(ATTR_MAX_TEMP) == MAX_TEMPERATURE
    assert state.attributes.get(ATTR_MIN_TEMP) == 5.0
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 19.0
    assert state.attributes.get(ATTR_TEMPERATURE) == 20.5
    assert state.attributes.get(VALVE_POSITION) == 25