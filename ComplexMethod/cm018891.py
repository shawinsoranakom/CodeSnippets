async def test_thermostat_state(
    spa, spa_state, setup_entry, hass: HomeAssistant
) -> None:
    """Test the thermostat entity initial state and attributes."""
    entity_id = f"climate.{spa.brand}_{spa.model}_thermostat"
    state = hass.states.get(entity_id)
    assert state
    assert state.state == HVACMode.HEAT
    assert set(state.attributes[ATTR_HVAC_MODES]) == {HVACMode.HEAT}
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.HEATING
    assert (
        state.attributes[ATTR_SUPPORTED_FEATURES]
        == ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.TARGET_TEMPERATURE
    )
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 38
    assert state.attributes[ATTR_TEMPERATURE] == 39
    assert state.attributes[ATTR_MAX_TEMP] == DEFAULT_MAX_TEMP
    assert state.attributes[ATTR_MIN_TEMP] == DEFAULT_MIN_TEMP
    assert state.attributes[ATTR_PRESET_MODES] == ["none", "eco", "day", "ready"]
    assert state.attributes.get(ATTR_PRESET_MODE) == PRESET_NONE