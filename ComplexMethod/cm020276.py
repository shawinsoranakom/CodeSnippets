async def test_thermostat_heat(
    hass: HomeAssistant, setup_platform: PlatformSetup, create_device: CreateDevice
) -> None:
    """Test a thermostat that is heating."""
    create_device.create(
        {
            "sdm.devices.traits.ThermostatHvac": {
                "status": "HEATING",
            },
            "sdm.devices.traits.ThermostatMode": {
                "availableModes": ["HEAT", "COOL", "HEATCOOL", "OFF"],
                "mode": "HEAT",
            },
            "sdm.devices.traits.Temperature": {
                "ambientTemperatureCelsius": 16.2,
            },
            "sdm.devices.traits.Humidity": {
                "ambientHumidityPercent": 40.6,
            },
            "sdm.devices.traits.ThermostatTemperatureSetpoint": {
                "heatCelsius": 22.0,
            },
        },
    )
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.HEAT
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.HEATING
    assert thermostat.attributes[ATTR_CURRENT_HUMIDITY] == 40.6
    assert thermostat.attributes[ATTR_CURRENT_TEMPERATURE] == 16.2
    assert set(thermostat.attributes[ATTR_HVAC_MODES]) == {
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
        HVACMode.OFF,
    }
    assert thermostat.attributes[ATTR_TEMPERATURE] == 22.0
    assert thermostat.attributes[ATTR_TARGET_TEMP_LOW] is None
    assert thermostat.attributes[ATTR_TARGET_TEMP_HIGH] is None
    assert ATTR_PRESET_MODE not in thermostat.attributes
    assert ATTR_PRESET_MODES not in thermostat.attributes