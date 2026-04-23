async def test_thermostat_eco_on(
    hass: HomeAssistant, setup_platform: PlatformSetup, create_device: CreateDevice
) -> None:
    """Test a thermostat in eco mode."""
    create_device.create(
        {
            "sdm.devices.traits.ThermostatHvac": {
                "status": "COOLING",
            },
            "sdm.devices.traits.ThermostatMode": {
                "availableModes": ["HEAT", "COOL", "HEATCOOL", "OFF"],
                "mode": "HEATCOOL",
            },
            "sdm.devices.traits.ThermostatEco": {
                "availableModes": ["MANUAL_ECO", "OFF"],
                "mode": "MANUAL_ECO",
                "heatCelsius": 21.0,
                "coolCelsius": 29.0,
            },
            "sdm.devices.traits.Temperature": {
                "ambientTemperatureCelsius": 29.9,
            },
            "sdm.devices.traits.ThermostatTemperatureSetpoint": {
                "heatCelsius": 22.0,
                "coolCelsius": 28.0,
            },
        },
    )
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.HEAT_COOL
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.COOLING
    assert thermostat.attributes[ATTR_CURRENT_TEMPERATURE] == 29.9
    assert set(thermostat.attributes[ATTR_HVAC_MODES]) == {
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
        HVACMode.OFF,
    }
    assert thermostat.attributes[ATTR_TARGET_TEMP_LOW] == 21.0
    assert thermostat.attributes[ATTR_TARGET_TEMP_HIGH] == 29.0
    assert thermostat.attributes[ATTR_TEMPERATURE] is None
    assert thermostat.attributes[ATTR_PRESET_MODE] == PRESET_ECO
    assert thermostat.attributes[ATTR_PRESET_MODES] == [PRESET_ECO, PRESET_NONE]