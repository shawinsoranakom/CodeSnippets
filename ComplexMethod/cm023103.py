async def test_thermostat_heatit_z_trm2fx(
    hass: HomeAssistant, client, climate_heatit_z_trm2fx, integration
) -> None:
    """Test a heatit Z-TRM2fx entity."""
    node = climate_heatit_z_trm2fx
    state = hass.states.get(CLIMATE_FLOOR_THERMOSTAT_ENTITY)

    assert state
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_HVAC_MODES] == [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
    ]
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 28.8
    assert state.attributes[ATTR_TEMPERATURE] == 29
    assert (
        state.attributes[ATTR_SUPPORTED_FEATURES]
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    assert state.attributes[ATTR_MIN_TEMP] == 0
    assert state.attributes[ATTR_MAX_TEMP] == 50

    # Try switching to external sensor
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 24,
            "args": {
                "commandClassName": "Configuration",
                "commandClass": 112,
                "endpoint": 0,
                "property": 2,
                "propertyName": "Sensor mode",
                "newValue": 4,
                "prevValue": 2,
            },
        },
    )
    node.receive_event(event)
    state = hass.states.get(CLIMATE_FLOOR_THERMOSTAT_ENTITY)
    assert state
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 0