async def test_heater_cooler_read_thermostat_state(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a HomeKit thermostat accessory."""
    helper = await setup_test_component(
        hass, get_next_aid(), create_heater_cooler_service
    )

    # Simulate that heating is on
    await helper.async_update(
        ServicesTypes.HEATER_COOLER,
        {
            CharacteristicsTypes.TEMPERATURE_CURRENT: 19,
            CharacteristicsTypes.TEMPERATURE_COOLING_THRESHOLD: 21,
            CharacteristicsTypes.CURRENT_HEATER_COOLER_STATE: CurrentHeaterCoolerStateValues.HEATING,
            CharacteristicsTypes.TARGET_HEATER_COOLER_STATE: TargetHeaterCoolerStateValues.HEAT,
            CharacteristicsTypes.SWING_MODE: SwingModeValues.DISABLED,
        },
    )

    state = await helper.poll_and_get_state()
    assert state.state == HVACMode.HEAT
    assert state.attributes["current_temperature"] == 19
    assert state.attributes["min_temp"] == 7
    assert state.attributes["max_temp"] == 35

    # Simulate that cooling is on
    await helper.async_update(
        ServicesTypes.HEATER_COOLER,
        {
            CharacteristicsTypes.TEMPERATURE_CURRENT: 21,
            CharacteristicsTypes.TEMPERATURE_COOLING_THRESHOLD: 19,
            CharacteristicsTypes.CURRENT_HEATER_COOLER_STATE: CurrentHeaterCoolerStateValues.COOLING,
            CharacteristicsTypes.TARGET_HEATER_COOLER_STATE: TargetHeaterCoolerStateValues.COOL,
            CharacteristicsTypes.SWING_MODE: SwingModeValues.DISABLED,
        },
    )

    state = await helper.poll_and_get_state()
    assert state.state == HVACMode.COOL
    assert state.attributes["current_temperature"] == 21

    # Simulate that we are in auto mode
    await helper.async_update(
        ServicesTypes.HEATER_COOLER,
        {
            CharacteristicsTypes.TEMPERATURE_CURRENT: 21,
            CharacteristicsTypes.TEMPERATURE_COOLING_THRESHOLD: 21,
            CharacteristicsTypes.CURRENT_HEATER_COOLER_STATE: CurrentHeaterCoolerStateValues.COOLING,
            CharacteristicsTypes.TARGET_HEATER_COOLER_STATE: TargetHeaterCoolerStateValues.AUTOMATIC,
            CharacteristicsTypes.SWING_MODE: SwingModeValues.DISABLED,
        },
    )

    state = await helper.poll_and_get_state()
    assert state.state == HVACMode.HEAT_COOL