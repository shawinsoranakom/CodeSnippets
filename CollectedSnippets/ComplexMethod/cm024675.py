async def test_climate_read_thermostat_state(
    hass: HomeAssistant, get_next_aid: Callable[[], int]
) -> None:
    """Test that we can read the state of a HomeKit thermostat accessory."""
    helper = await setup_test_component(hass, get_next_aid(), create_thermostat_service)

    # Simulate that heating is on
    await helper.async_update(
        ServicesTypes.THERMOSTAT,
        {
            CharacteristicsTypes.TEMPERATURE_CURRENT: 19,
            CharacteristicsTypes.TEMPERATURE_TARGET: 21,
            CharacteristicsTypes.HEATING_COOLING_CURRENT: 1,
            CharacteristicsTypes.HEATING_COOLING_TARGET: 1,
            CharacteristicsTypes.RELATIVE_HUMIDITY_CURRENT: 50,
            CharacteristicsTypes.RELATIVE_HUMIDITY_TARGET: 45,
        },
    )

    state = await helper.poll_and_get_state()
    assert state.state == HVACMode.HEAT
    assert state.attributes["current_temperature"] == 19
    assert state.attributes["current_humidity"] == 50
    assert state.attributes["min_temp"] == 7
    assert state.attributes["max_temp"] == 35

    # Simulate that cooling is on
    await helper.async_update(
        ServicesTypes.THERMOSTAT,
        {
            CharacteristicsTypes.TEMPERATURE_CURRENT: 21,
            CharacteristicsTypes.TEMPERATURE_TARGET: 19,
            CharacteristicsTypes.HEATING_COOLING_CURRENT: 2,
            CharacteristicsTypes.HEATING_COOLING_TARGET: 2,
            CharacteristicsTypes.RELATIVE_HUMIDITY_CURRENT: 45,
            CharacteristicsTypes.RELATIVE_HUMIDITY_TARGET: 45,
        },
    )

    state = await helper.poll_and_get_state()
    assert state.state == HVACMode.COOL
    assert state.attributes["current_temperature"] == 21
    assert state.attributes["current_humidity"] == 45

    # Simulate that we are in heat/cool mode
    await helper.async_update(
        ServicesTypes.THERMOSTAT,
        {
            CharacteristicsTypes.TEMPERATURE_CURRENT: 21,
            CharacteristicsTypes.TEMPERATURE_TARGET: 21,
            CharacteristicsTypes.HEATING_COOLING_CURRENT: 0,
            CharacteristicsTypes.HEATING_COOLING_TARGET: 3,
        },
    )

    state = await helper.poll_and_get_state()
    assert state.state == HVACMode.HEAT_COOL