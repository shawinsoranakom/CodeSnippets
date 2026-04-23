async def test_set_temperature_heat(hass: HomeAssistant, device_climate_mock) -> None:
    """Test setting temperature service call in heating HVAC mode."""

    device_climate = await device_climate_mock(
        CLIMATE_SINOPE,
        {
            "occupied_cooling_setpoint": 2500,
            "occupied_heating_setpoint": 2000,
            "system_mode": Thermostat.SystemMode.Heat,
            "unoccupied_heating_setpoint": 1600,
            "unoccupied_cooling_setpoint": 2700,
        },
        manuf=MANUF_SINOPE,
        quirk=zhaquirks.sinope.thermostat.SinopeTechnologiesThermostat,
    )
    entity_id = find_entity_id(Platform.CLIMATE, device_climate, hass)
    thrm_cluster = device_climate.device.device.endpoints[1].thermostat

    state = hass.states.get(entity_id)
    assert state.state == HVACMode.HEAT

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_TARGET_TEMP_HIGH: 30,
            ATTR_TARGET_TEMP_LOW: 15,
        },
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_TARGET_TEMP_LOW] is None
    assert state.attributes[ATTR_TARGET_TEMP_HIGH] is None
    assert state.attributes[ATTR_TEMPERATURE] == 20.0
    assert thrm_cluster.write_attributes.await_count == 0

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 21},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_TARGET_TEMP_LOW] is None
    assert state.attributes[ATTR_TARGET_TEMP_HIGH] is None
    assert state.attributes[ATTR_TEMPERATURE] == 21.0
    assert thrm_cluster.write_attributes.await_count == 1
    assert thrm_cluster.write_attributes.call_args_list[0][0][0] == {
        "occupied_heating_setpoint": 2100
    }

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_PRESET_MODE: PRESET_AWAY},
        blocking=True,
    )
    thrm_cluster.write_attributes.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 22},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_TARGET_TEMP_LOW] is None
    assert state.attributes[ATTR_TARGET_TEMP_HIGH] is None
    assert state.attributes[ATTR_TEMPERATURE] == 22.0
    assert thrm_cluster.write_attributes.await_count == 1
    assert thrm_cluster.write_attributes.call_args_list[0][0][0] == {
        "unoccupied_heating_setpoint": 2200
    }