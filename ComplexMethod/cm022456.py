async def test_temperature_setting_climate_setpoint(hass: HomeAssistant) -> None:
    """Test TemperatureSetting trait support for climate domain - setpoint."""
    assert helpers.get_google_type(climate.DOMAIN, None) is not None
    assert trait.TemperatureSettingTrait.supported(climate.DOMAIN, 0, None, None)

    trt = trait.TemperatureSettingTrait(
        hass,
        State(
            "climate.bla",
            climate.HVACMode.COOL,
            {
                ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
                climate.ATTR_HVAC_MODES: [STATE_OFF, climate.HVACMode.COOL],
                climate.ATTR_MIN_TEMP: 10,
                climate.ATTR_MAX_TEMP: 30,
                climate.ATTR_PRESET_MODE: climate.PRESET_ECO,
                ATTR_TEMPERATURE: 18,
                climate.ATTR_CURRENT_TEMPERATURE: 20,
            },
        ),
        BASIC_CONFIG,
    )
    assert trt.sync_attributes() == {
        "availableThermostatModes": ["off", "cool", "on"],
        "thermostatTemperatureRange": {
            "minThresholdCelsius": 10,
            "maxThresholdCelsius": 30,
        },
        "thermostatTemperatureUnit": "C",
    }
    assert trt.query_attributes() == {
        "thermostatMode": "eco",
        "thermostatTemperatureAmbient": 20,
        "thermostatTemperatureSetpoint": 18,
    }
    assert trt.can_execute(trait.COMMAND_THERMOSTAT_TEMPERATURE_SETPOINT, {})
    assert trt.can_execute(trait.COMMAND_THERMOSTAT_SET_MODE, {})

    calls = async_mock_service(hass, climate.DOMAIN, climate.SERVICE_SET_TEMPERATURE)
    with pytest.raises(helpers.SmartHomeError):
        await trt.execute(
            trait.COMMAND_THERMOSTAT_TEMPERATURE_SETPOINT,
            BASIC_DATA,
            {"thermostatTemperatureSetpoint": -100},
            {},
        )

    await trt.execute(
        trait.COMMAND_THERMOSTAT_TEMPERATURE_SETPOINT,
        BASIC_DATA,
        {"thermostatTemperatureSetpoint": 19},
        {},
    )
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "climate.bla", ATTR_TEMPERATURE: 19}

    calls = async_mock_service(hass, climate.DOMAIN, climate.SERVICE_SET_PRESET_MODE)
    await trt.execute(
        trait.COMMAND_THERMOSTAT_SET_MODE,
        BASIC_DATA,
        {"thermostatMode": "eco"},
        {},
    )
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "climate.bla",
        climate.ATTR_PRESET_MODE: "eco",
    }

    calls = async_mock_service(hass, climate.DOMAIN, climate.SERVICE_SET_TEMPERATURE)
    await trt.execute(
        trait.COMMAND_THERMOSTAT_TEMPERATURE_SET_RANGE,
        BASIC_DATA,
        {
            "thermostatTemperatureSetpointHigh": 15,
            "thermostatTemperatureSetpointLow": 22,
        },
        {},
    )
    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "climate.bla", ATTR_TEMPERATURE: 18.5}