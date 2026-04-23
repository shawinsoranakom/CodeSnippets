async def test_thermostat_target_temp(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    create_device: CreateDevice,
    create_event: CreateEvent,
) -> None:
    """Test a thermostat changing hvac modes and affected on target temps."""
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
                "ambientTemperatureCelsius": 20.1,
            },
            "sdm.devices.traits.ThermostatTemperatureSetpoint": {
                "heatCelsius": 23.0,
            },
        }
    )
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.HEAT
    assert thermostat.attributes[ATTR_TEMPERATURE] == 23.0
    assert thermostat.attributes[ATTR_TARGET_TEMP_LOW] is None
    assert thermostat.attributes[ATTR_TARGET_TEMP_HIGH] is None

    # Simulate pubsub message changing modes
    await create_event(
        {
            "sdm.devices.traits.ThermostatMode": {
                "availableModes": ["HEAT", "COOL", "HEATCOOL", "OFF"],
                "mode": "HEATCOOL",
            },
            "sdm.devices.traits.ThermostatTemperatureSetpoint": {
                "heatCelsius": 22.0,
                "coolCelsius": 28.0,
            },
        }
    )

    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.HEAT_COOL
    assert thermostat.attributes[ATTR_TARGET_TEMP_LOW] == 22.0
    assert thermostat.attributes[ATTR_TARGET_TEMP_HIGH] == 28.0
    assert thermostat.attributes[ATTR_TEMPERATURE] is None