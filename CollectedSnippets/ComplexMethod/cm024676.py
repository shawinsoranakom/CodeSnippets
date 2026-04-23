async def test_hvac_mode_vs_hvac_action(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Check that we haven't conflated hvac_mode and hvac_action."""
    helper = await setup_test_component(hass, get_next_aid(), create_thermostat_service)

    # Simulate that current temperature is above target temp
    # Heating might be on, but hvac_action currently 'off'
    await helper.async_update(
        ServicesTypes.THERMOSTAT,
        {
            CharacteristicsTypes.TEMPERATURE_CURRENT: 22,
            CharacteristicsTypes.TEMPERATURE_TARGET: 21,
            CharacteristicsTypes.HEATING_COOLING_CURRENT: 0,
            CharacteristicsTypes.HEATING_COOLING_TARGET: 1,
            CharacteristicsTypes.RELATIVE_HUMIDITY_CURRENT: 50,
            CharacteristicsTypes.RELATIVE_HUMIDITY_TARGET: 45,
        },
    )

    state = await helper.poll_and_get_state()
    assert state.state == "heat"
    assert state.attributes["hvac_action"] == "idle"

    # Simulate the fan running while the heat/cool is idle
    await helper.async_update(
        ServicesTypes.THERMOSTAT,
        {
            CharacteristicsTypes.FAN_STATE_CURRENT: CurrentFanStateValues.ACTIVE,
        },
    )

    state = await helper.poll_and_get_state()
    assert state.state == "heat"
    assert state.attributes["hvac_action"] == HVACAction.FAN

    # Simulate that current temperature is below target temp
    # Heating might be on and hvac_action currently 'heat'
    await helper.async_update(
        ServicesTypes.THERMOSTAT,
        {
            CharacteristicsTypes.TEMPERATURE_CURRENT: 19,
            CharacteristicsTypes.HEATING_COOLING_CURRENT: 1,
        },
    )

    state = await helper.poll_and_get_state()
    assert state.state == "heat"
    assert state.attributes["hvac_action"] == HVACAction.HEATING

    # If the fan is active, and the heating is off, the hvac_action should be 'fan'
    # and not 'idle' or 'heating'
    await helper.async_update(
        ServicesTypes.THERMOSTAT,
        {
            CharacteristicsTypes.FAN_STATE_CURRENT: CurrentFanStateValues.ACTIVE,
            CharacteristicsTypes.HEATING_COOLING_CURRENT: HeatingCoolingCurrentValues.IDLE,
            CharacteristicsTypes.HEATING_COOLING_TARGET: HeatingCoolingTargetValues.OFF,
            CharacteristicsTypes.FAN_STATE_CURRENT: CurrentFanStateValues.ACTIVE,
        },
    )

    state = await helper.poll_and_get_state()
    assert state.state == HVACMode.OFF
    assert state.attributes["hvac_action"] == HVACAction.FAN