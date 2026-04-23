async def test_thermostat_fan_empty(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    create_device: CreateDevice,
) -> None:
    """Test a fan trait with an empty response."""
    create_device.create(
        {
            "sdm.devices.traits.Fan": {},
            "sdm.devices.traits.ThermostatHvac": {"status": "OFF"},
            "sdm.devices.traits.ThermostatMode": {
                "availableModes": ["HEAT", "COOL", "HEATCOOL", "OFF"],
                "mode": "OFF",
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
    assert thermostat.state == HVACMode.OFF
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF
    assert thermostat.attributes[ATTR_CURRENT_HUMIDITY] == 40.6
    assert thermostat.attributes[ATTR_CURRENT_TEMPERATURE] == 16.2
    assert set(thermostat.attributes[ATTR_HVAC_MODES]) == {
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
        HVACMode.OFF,
    }
    assert ATTR_FAN_MODE not in thermostat.attributes
    assert ATTR_FAN_MODES not in thermostat.attributes
    assert thermostat.attributes[ATTR_SUPPORTED_FEATURES] == (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    # Ignores set_fan_mode since it is lacking SUPPORT_FAN_MODE
    await common.async_set_fan_mode(hass, FAN_ON)
    await hass.async_block_till_done()

    assert ATTR_FAN_MODE not in thermostat.attributes
    assert ATTR_FAN_MODES not in thermostat.attributes