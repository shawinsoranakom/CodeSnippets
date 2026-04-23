async def test_airzone_create_climates(hass: HomeAssistant) -> None:
    """Test creation of climates."""

    await async_init_integration(hass)

    # Aidoos
    state = hass.states.get("climate.bron")
    assert state.state == HVACMode.OFF
    assert ATTR_CURRENT_HUMIDITY not in state.attributes
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 21.0
    assert state.attributes[ATTR_FAN_MODE] == FAN_HIGH
    assert state.attributes[ATTR_FAN_MODES] == [
        FAN_LOW,
        FAN_MEDIUM,
        FAN_HIGH,
    ]
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF
    assert state.attributes[ATTR_HVAC_MODES] == [
        HVACMode.HEAT_COOL,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.FAN_ONLY,
        HVACMode.DRY,
        HVACMode.OFF,
    ]
    assert state.attributes[ATTR_MAX_TEMP] == 30
    assert state.attributes[ATTR_MIN_TEMP] == 15
    assert state.attributes[ATTR_TARGET_TEMP_STEP] == API_DEFAULT_TEMP_STEP
    assert state.attributes[ATTR_TEMPERATURE] == 22.0

    state = hass.states.get("climate.bron_pro")
    assert state.state == HVACMode.COOL
    assert ATTR_CURRENT_HUMIDITY not in state.attributes
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 20.0
    assert state.attributes[ATTR_FAN_MODE] == "60%"
    assert state.attributes[ATTR_FAN_MODES] == [
        FAN_AUTO,
        "20%",
        "40%",
        "60%",
        "80%",
        "100%",
    ]
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.COOLING
    assert state.attributes[ATTR_HVAC_MODES] == [
        HVACMode.HEAT_COOL,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.FAN_ONLY,
        HVACMode.DRY,
        HVACMode.OFF,
    ]
    assert state.attributes[ATTR_MAX_TEMP] == 30
    assert state.attributes[ATTR_MIN_TEMP] == 15
    assert state.attributes[ATTR_TARGET_TEMP_STEP] == API_DEFAULT_TEMP_STEP
    assert state.attributes.get(ATTR_TEMPERATURE) == 22.0

    # Groups
    state = hass.states.get("climate.group")
    assert state.state == HVACMode.COOL
    assert state.attributes[ATTR_CURRENT_HUMIDITY] == 27
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 22.5
    assert ATTR_FAN_MODE not in state.attributes
    assert ATTR_FAN_MODES not in state.attributes
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.COOLING
    assert state.attributes[ATTR_HVAC_MODES] == [
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.FAN_ONLY,
        HVACMode.DRY,
        HVACMode.OFF,
    ]
    assert state.attributes[ATTR_MAX_TEMP] == 30
    assert state.attributes[ATTR_MIN_TEMP] == 15
    assert state.attributes[ATTR_TARGET_TEMP_STEP] == API_DEFAULT_TEMP_STEP
    assert state.attributes[ATTR_TEMPERATURE] == 24.0

    # Installations
    state = hass.states.get("climate.house")
    assert state.state == HVACMode.COOL
    assert state.attributes[ATTR_CURRENT_HUMIDITY] == 27
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 21.5
    assert ATTR_FAN_MODE not in state.attributes
    assert ATTR_FAN_MODES not in state.attributes
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.COOLING
    assert state.attributes[ATTR_HVAC_MODES] == [
        HVACMode.HEAT_COOL,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.FAN_ONLY,
        HVACMode.DRY,
        HVACMode.OFF,
    ]
    assert state.attributes[ATTR_MAX_TEMP] == 30
    assert state.attributes[ATTR_MIN_TEMP] == 15
    assert state.attributes[ATTR_TARGET_TEMP_STEP] == API_DEFAULT_TEMP_STEP
    assert state.attributes[ATTR_TEMPERATURE] == 23.0

    # Zones
    state = hass.states.get("climate.dormitorio")
    assert state.state == HVACMode.OFF
    assert state.attributes[ATTR_CURRENT_HUMIDITY] == 24
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 25.0
    assert ATTR_FAN_MODE not in state.attributes
    assert ATTR_FAN_MODES not in state.attributes
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF
    assert state.attributes[ATTR_HVAC_MODES] == [
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.FAN_ONLY,
        HVACMode.DRY,
        HVACMode.OFF,
    ]
    assert state.attributes[ATTR_MAX_TEMP] == 30
    assert state.attributes[ATTR_MIN_TEMP] == 15
    assert state.attributes[ATTR_TARGET_TEMP_STEP] == API_DEFAULT_TEMP_STEP
    assert state.attributes[ATTR_TEMPERATURE] == 24.0

    state = hass.states.get("climate.salon")
    assert state.state == HVACMode.COOL
    assert state.attributes[ATTR_CURRENT_HUMIDITY] == 30
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 20.0
    assert ATTR_FAN_MODE not in state.attributes
    assert ATTR_FAN_MODES not in state.attributes
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.COOLING
    assert state.attributes[ATTR_HVAC_MODES] == [
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.FAN_ONLY,
        HVACMode.DRY,
        HVACMode.OFF,
    ]
    assert state.attributes[ATTR_MAX_TEMP] == 30
    assert state.attributes[ATTR_MIN_TEMP] == 15
    assert state.attributes[ATTR_TARGET_TEMP_STEP] == API_DEFAULT_TEMP_STEP
    assert state.attributes[ATTR_TEMPERATURE] == 24.0