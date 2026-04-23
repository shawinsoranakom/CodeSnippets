async def test_thermostat_set_temperature_hvac_mode(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    auth: FakeAuth,
    create_device: CreateDevice,
) -> None:
    """Test setting HVAC mode while setting temperature."""
    create_device.create(
        {
            "sdm.devices.traits.ThermostatHvac": {"status": "OFF"},
            "sdm.devices.traits.ThermostatMode": {
                "availableModes": ["HEAT", "COOL", "HEATCOOL", "OFF"],
                "mode": "OFF",
            },
            "sdm.devices.traits.ThermostatTemperatureSetpoint": {
                "coolCelsius": 25.0,
            },
        },
    )
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.OFF

    await common.async_set_temperature(hass, temperature=24.0, hvac_mode=HVACMode.COOL)
    await hass.async_block_till_done()

    assert auth.method == "post"
    assert auth.url == DEVICE_COMMAND
    assert auth.json == {
        "command": "sdm.devices.commands.ThermostatTemperatureSetpoint.SetCool",
        "params": {"coolCelsius": 24.0},
    }

    await common.async_set_temperature(hass, temperature=26.0, hvac_mode=HVACMode.HEAT)
    await hass.async_block_till_done()

    assert auth.method == "post"
    assert auth.url == DEVICE_COMMAND
    assert auth.json == {
        "command": "sdm.devices.commands.ThermostatTemperatureSetpoint.SetHeat",
        "params": {"heatCelsius": 26.0},
    }

    await common.async_set_temperature(
        hass, target_temp_low=20.0, target_temp_high=24.0, hvac_mode=HVACMode.HEAT_COOL
    )
    await hass.async_block_till_done()

    assert auth.method == "post"
    assert auth.url == DEVICE_COMMAND
    assert auth.json == {
        "command": "sdm.devices.commands.ThermostatTemperatureSetpoint.SetRange",
        "params": {"heatCelsius": 20.0, "coolCelsius": 24.0},
    }