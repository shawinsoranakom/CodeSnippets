async def test_thermostat_fan_on(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    create_device: CreateDevice,
) -> None:
    """Test a thermostat with the fan running."""
    create_device.create(
        {
            "sdm.devices.traits.Fan": {
                "timerMode": "ON",
                "timerTimeout": "2019-05-10T03:22:54Z",
            },
            "sdm.devices.traits.ThermostatHvac": {
                "status": "OFF",
            },
            "sdm.devices.traits.ThermostatMode": {
                "availableModes": ["HEAT", "COOL", "HEATCOOL", "OFF"],
                "mode": "COOL",
            },
            "sdm.devices.traits.Temperature": {
                "ambientTemperatureCelsius": 16.2,
            },
            "sdm.devices.traits.Humidity": {
                "ambientHumidityPercent": 40.6,
            },
        }
    )
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.COOL
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    assert thermostat.attributes[ATTR_CURRENT_HUMIDITY] == 40.6
    assert thermostat.attributes[ATTR_CURRENT_TEMPERATURE] == 16.2
    assert set(thermostat.attributes[ATTR_HVAC_MODES]) == {
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
        HVACMode.OFF,
    }
    assert thermostat.attributes[ATTR_FAN_MODE] == FAN_ON
    assert thermostat.attributes[ATTR_FAN_MODES] == [FAN_ON, FAN_OFF]
    assert thermostat.attributes[ATTR_SUPPORTED_FEATURES] == (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )