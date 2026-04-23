async def test_thermostat_heatit_z_trm6(
    hass: HomeAssistant, client, climate_heatit_z_trm6, integration
) -> None:
    """Test a heatit Z-TRM6 entity."""
    node = climate_heatit_z_trm6
    state = hass.states.get(CLIMATE_FLOOR_THERMOSTAT_ENTITY)

    assert state
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_HVAC_MODES] == [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
    ]
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 22.5
    assert state.attributes[ATTR_TEMPERATURE] == 19
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    assert (
        state.attributes[ATTR_SUPPORTED_FEATURES]
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    assert state.attributes[ATTR_MIN_TEMP] == 5
    assert state.attributes[ATTR_MAX_TEMP] == 40

    # Try switching to external sensor (not connected so defaults to 0)
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 101,
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

    # Try switching to floor sensor
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 101,
            "args": {
                "commandClassName": "Configuration",
                "commandClass": 112,
                "endpoint": 0,
                "property": 2,
                "propertyName": "Sensor mode",
                "newValue": 0,
                "prevValue": 4,
            },
        },
    )
    node.receive_event(event)
    state = hass.states.get(CLIMATE_FLOOR_THERMOSTAT_ENTITY)
    assert state
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 21.9