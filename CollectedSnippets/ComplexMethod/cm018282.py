async def test_airzone_create_climates(hass: HomeAssistant) -> None:
    """Test creation of climates."""

    await async_init_integration(hass)

    state = hass.states.get("climate.despacho")
    assert state.state == HVACMode.OFF
    assert state.attributes.get(ATTR_CURRENT_HUMIDITY) == 36
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 21.2
    assert state.attributes.get(ATTR_FAN_MODE) is None
    assert state.attributes.get(ATTR_FAN_MODES) is None
    assert state.attributes.get(ATTR_HVAC_ACTION) == HVACAction.OFF
    assert state.attributes.get(ATTR_HVAC_MODES) == [
        HVACMode.OFF,
        HVACMode.FAN_ONLY,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
    ]
    assert state.attributes.get(ATTR_MAX_TEMP) == 30
    assert state.attributes.get(ATTR_MIN_TEMP) == 15
    assert state.attributes.get(ATTR_TARGET_TEMP_STEP) == API_TEMPERATURE_STEP
    assert state.attributes.get(ATTR_TEMPERATURE) == 19.4

    state = hass.states.get("climate.dorm_1")
    assert state.state == HVACMode.HEAT
    assert state.attributes.get(ATTR_CURRENT_HUMIDITY) == 35
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 20.8
    assert state.attributes.get(ATTR_FAN_MODE) is None
    assert state.attributes.get(ATTR_FAN_MODES) is None
    assert state.attributes.get(ATTR_HVAC_ACTION) == HVACAction.IDLE
    assert state.attributes.get(ATTR_HVAC_MODES) == [
        HVACMode.OFF,
        HVACMode.FAN_ONLY,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
    ]
    assert state.attributes.get(ATTR_MAX_TEMP) == 30
    assert state.attributes.get(ATTR_MIN_TEMP) == 15
    assert state.attributes.get(ATTR_TARGET_TEMP_STEP) == API_TEMPERATURE_STEP
    assert state.attributes.get(ATTR_TEMPERATURE) == 19.3

    state = hass.states.get("climate.dorm_2")
    assert state.state == HVACMode.OFF
    assert state.attributes.get(ATTR_CURRENT_HUMIDITY) == 40
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 20.5
    assert state.attributes.get(ATTR_FAN_MODE) is None
    assert state.attributes.get(ATTR_FAN_MODES) is None
    assert state.attributes.get(ATTR_HVAC_ACTION) == HVACAction.OFF
    assert state.attributes.get(ATTR_HVAC_MODES) == [
        HVACMode.OFF,
        HVACMode.FAN_ONLY,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
    ]
    assert state.attributes.get(ATTR_MAX_TEMP) == 30
    assert state.attributes.get(ATTR_MIN_TEMP) == 15
    assert state.attributes.get(ATTR_TARGET_TEMP_STEP) == API_TEMPERATURE_STEP
    assert state.attributes.get(ATTR_TEMPERATURE) == 19.5

    state = hass.states.get("climate.dorm_ppal")
    assert state.state == HVACMode.HEAT
    assert state.attributes.get(ATTR_CURRENT_HUMIDITY) == 39
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 21.1
    assert state.attributes.get(ATTR_FAN_MODE) == FAN_AUTO
    assert state.attributes.get(ATTR_FAN_MODES) == [
        FAN_AUTO,
        FAN_LOW,
        FAN_HIGH,
    ]
    assert state.attributes.get(ATTR_HVAC_ACTION) == HVACAction.HEATING
    assert state.attributes.get(ATTR_HVAC_MODES) == [
        HVACMode.OFF,
        HVACMode.FAN_ONLY,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
    ]
    assert state.attributes.get(ATTR_MAX_TEMP) == 30
    assert state.attributes.get(ATTR_MIN_TEMP) == 15
    assert state.attributes.get(ATTR_TARGET_TEMP_STEP) == API_TEMPERATURE_STEP
    assert state.attributes.get(ATTR_TEMPERATURE) == 19.2

    state = hass.states.get("climate.salon")
    assert state.state == HVACMode.OFF
    assert state.attributes.get(ATTR_CURRENT_HUMIDITY) == 34
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 19.6
    assert state.attributes.get(ATTR_FAN_MODE) == FAN_AUTO
    assert state.attributes.get(ATTR_FAN_MODES) == [
        FAN_AUTO,
        FAN_LOW,
        FAN_MEDIUM,
        FAN_HIGH,
    ]
    assert state.attributes.get(ATTR_HVAC_ACTION) == HVACAction.OFF
    assert state.attributes.get(ATTR_HVAC_MODES) == [
        HVACMode.OFF,
        HVACMode.FAN_ONLY,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
    ]
    assert state.attributes.get(ATTR_MAX_TEMP) == 30
    assert state.attributes.get(ATTR_MIN_TEMP) == 15
    assert state.attributes.get(ATTR_TARGET_TEMP_STEP) == API_TEMPERATURE_STEP
    assert state.attributes.get(ATTR_TEMPERATURE) == 19.1

    state = hass.states.get("climate.airzone_2_1")
    assert state.state == HVACMode.OFF
    assert state.attributes.get(ATTR_CURRENT_HUMIDITY) == 62
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 22.3
    assert state.attributes.get(ATTR_FAN_MODE) == FAN_AUTO
    assert state.attributes.get(ATTR_FAN_MODES) == [
        FAN_AUTO,
        FAN_LOW,
        FAN_MEDIUM,
        "75%",
        FAN_HIGH,
    ]
    assert state.attributes.get(ATTR_HVAC_ACTION) == HVACAction.OFF
    assert state.attributes.get(ATTR_HVAC_MODES) == [
        HVACMode.HEAT_COOL,
        HVACMode.OFF,
    ]
    assert state.attributes.get(ATTR_MAX_TEMP) == 30
    assert state.attributes.get(ATTR_MIN_TEMP) == 15
    assert state.attributes.get(ATTR_TARGET_TEMP_STEP) == API_TEMPERATURE_STEP
    assert state.attributes.get(ATTR_TEMPERATURE) == 19.0

    state = hass.states.get("climate.dkn_plus")
    assert state.state == HVACMode.HEAT_COOL
    assert state.attributes.get(ATTR_CURRENT_HUMIDITY) is None
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 21.7
    assert state.attributes.get(ATTR_FAN_MODE) == "40%"
    assert state.attributes.get(ATTR_FAN_MODES) == [
        FAN_AUTO,
        FAN_LOW,
        "40%",
        FAN_MEDIUM,
        "80%",
        FAN_HIGH,
    ]
    assert state.attributes.get(ATTR_HVAC_ACTION) == HVACAction.COOLING
    assert state.attributes.get(ATTR_HVAC_MODES) == [
        HVACMode.FAN_ONLY,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
        HVACMode.HEAT_COOL,
        HVACMode.OFF,
    ]
    assert state.attributes.get(ATTR_MAX_TEMP) == 32.2
    assert state.attributes.get(ATTR_MIN_TEMP) == 17.8
    assert state.attributes.get(ATTR_TARGET_TEMP_STEP) == API_TEMPERATURE_STEP
    assert state.attributes.get(ATTR_TARGET_TEMP_HIGH) == 25.0
    assert state.attributes.get(ATTR_TARGET_TEMP_LOW) == 22.8

    state = hass.states.get("climate.aux_heat")
    assert state.state == HVACMode.HEAT
    assert state.attributes.get(ATTR_CURRENT_HUMIDITY) is None
    assert state.attributes.get(ATTR_CURRENT_TEMPERATURE) == 22
    assert state.attributes.get(ATTR_HVAC_ACTION) == HVACAction.IDLE
    assert state.attributes.get(ATTR_HVAC_MODES) == [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.FAN_ONLY,
        HVACMode.DRY,
    ]
    assert state.attributes.get(ATTR_MAX_TEMP) == 30
    assert state.attributes.get(ATTR_MIN_TEMP) == 15
    assert state.attributes.get(ATTR_TARGET_TEMP_STEP) == API_TEMPERATURE_STEP
    assert state.attributes.get(ATTR_TEMPERATURE) == 20.0

    HVAC_MOCK_CHANGED = copy.deepcopy(HVAC_MOCK)
    HVAC_MOCK_CHANGED[API_SYSTEMS][0][API_DATA][0][API_MAX_TEMP] = 25
    HVAC_MOCK_CHANGED[API_SYSTEMS][0][API_DATA][0][API_MIN_TEMP] = 10

    with (
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_dhw",
            return_value=HVAC_DHW_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac",
            return_value=HVAC_MOCK_CHANGED,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac_systems",
            return_value=HVAC_SYSTEMS_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_webserver",
            return_value=HVAC_WEBSERVER_MOCK,
        ),
    ):
        async_fire_time_changed(hass, utcnow() + SCAN_INTERVAL)
        await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("climate.salon")
    assert state.attributes.get(ATTR_MAX_TEMP) == 25
    assert state.attributes.get(ATTR_MIN_TEMP) == 10