async def test_temperature_setting_climate_range(hass: HomeAssistant) -> None:
    """Test TemperatureSetting trait support for climate domain - range."""
    assert helpers.get_google_type(climate.DOMAIN, None) is not None
    assert trait.TemperatureSettingTrait.supported(climate.DOMAIN, 0, None, None)

    hass.config.units = US_CUSTOMARY_SYSTEM

    trt = trait.TemperatureSettingTrait(
        hass,
        State(
            "climate.bla",
            climate.HVACMode.AUTO,
            {
                climate.ATTR_CURRENT_TEMPERATURE: 70,
                climate.ATTR_CURRENT_HUMIDITY: 25,
                ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
                climate.ATTR_HVAC_MODES: [
                    STATE_OFF,
                    climate.HVACMode.COOL,
                    climate.HVACMode.HEAT,
                    climate.HVACMode.AUTO,
                ],
                climate.ATTR_TARGET_TEMP_HIGH: 75,
                climate.ATTR_TARGET_TEMP_LOW: 65,
                climate.ATTR_MIN_TEMP: 50,
                climate.ATTR_MAX_TEMP: 80,
            },
        ),
        BASIC_CONFIG,
    )
    assert trt.sync_attributes() == {
        "availableThermostatModes": ["off", "cool", "heat", "auto", "on"],
        "thermostatTemperatureRange": {
            "minThresholdCelsius": 10,
            "maxThresholdCelsius": 26.7,
        },
        "thermostatTemperatureUnit": "F",
    }
    assert trt.query_attributes() == {
        "thermostatMode": "auto",
        "thermostatTemperatureAmbient": 21.1,
        "thermostatHumidityAmbient": 25,
        "thermostatTemperatureSetpointLow": 18.3,
        "thermostatTemperatureSetpointHigh": 23.9,
    }
    assert trt.can_execute(trait.COMMAND_THERMOSTAT_TEMPERATURE_SET_RANGE, {})
    assert trt.can_execute(trait.COMMAND_THERMOSTAT_SET_MODE, {})

    calls = async_mock_service(hass, climate.DOMAIN, climate.SERVICE_SET_TEMPERATURE)
    await trt.execute(
        trait.COMMAND_THERMOSTAT_TEMPERATURE_SET_RANGE,
        BASIC_DATA,
        {
            "thermostatTemperatureSetpointHigh": 25,
            "thermostatTemperatureSetpointLow": 20,
        },
        {},
    )
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "climate.bla",
        climate.ATTR_TARGET_TEMP_HIGH: 77,
        climate.ATTR_TARGET_TEMP_LOW: 68,
    }

    calls = async_mock_service(hass, climate.DOMAIN, climate.SERVICE_SET_HVAC_MODE)
    await trt.execute(
        trait.COMMAND_THERMOSTAT_SET_MODE, BASIC_DATA, {"thermostatMode": "cool"}, {}
    )
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "climate.bla",
        climate.ATTR_HVAC_MODE: climate.HVACMode.COOL,
    }

    with pytest.raises(helpers.SmartHomeError) as err:
        await trt.execute(
            trait.COMMAND_THERMOSTAT_TEMPERATURE_SET_RANGE,
            BASIC_DATA,
            {
                "thermostatTemperatureSetpointHigh": 26,
                "thermostatTemperatureSetpointLow": -100,
            },
            {},
        )
    assert err.value.code == const.ERR_VALUE_OUT_OF_RANGE

    with pytest.raises(helpers.SmartHomeError) as err:
        await trt.execute(
            trait.COMMAND_THERMOSTAT_TEMPERATURE_SET_RANGE,
            BASIC_DATA,
            {
                "thermostatTemperatureSetpointHigh": 100,
                "thermostatTemperatureSetpointLow": 18,
            },
            {},
        )
    assert err.value.code == const.ERR_VALUE_OUT_OF_RANGE

    calls = async_mock_service(hass, climate.DOMAIN, climate.SERVICE_SET_TEMPERATURE)
    await trt.execute(
        trait.COMMAND_THERMOSTAT_TEMPERATURE_SETPOINT,
        BASIC_DATA,
        {"thermostatTemperatureSetpoint": 23.9},
        {},
    )
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "climate.bla",
        climate.ATTR_TEMPERATURE: 75,
    }