async def test_thermostat_eco_heat_only(
    hass: HomeAssistant, setup_platform: PlatformSetup, create_device: CreateDevice
) -> None:
    """Test a thermostat in eco mode that only supports heat."""
    create_device.create(
        {
            "sdm.devices.traits.ThermostatHvac": {
                "status": "OFF",
            },
            "sdm.devices.traits.ThermostatMode": {
                "availableModes": ["HEAT", "OFF"],
                "mode": "HEAT",
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
            "sdm.devices.traits.ThermostatTemperatureSetpoint": {},
        },
    )
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.HEAT
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    assert thermostat.attributes[ATTR_CURRENT_TEMPERATURE] == 29.9
    assert set(thermostat.attributes[ATTR_HVAC_MODES]) == {
        HVACMode.HEAT,
        HVACMode.OFF,
    }
    assert thermostat.attributes[ATTR_TEMPERATURE] == 21.0
    assert ATTR_TARGET_TEMP_LOW not in thermostat.attributes
    assert ATTR_TARGET_TEMP_HIGH not in thermostat.attributes
    assert thermostat.attributes[ATTR_PRESET_MODE] == PRESET_ECO
    assert thermostat.attributes[ATTR_PRESET_MODES] == [PRESET_ECO, PRESET_NONE]