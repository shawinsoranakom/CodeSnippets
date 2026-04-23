async def test_thermostat_set_fan(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    auth: FakeAuth,
    create_device: CreateDevice,
) -> None:
    """Test a thermostat enabling the fan."""
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
                "mode": "HEAT",
            },
        }
    )
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.HEAT
    assert thermostat.attributes[ATTR_FAN_MODE] == FAN_ON
    assert thermostat.attributes[ATTR_FAN_MODES] == [FAN_ON, FAN_OFF]
    assert thermostat.attributes[ATTR_SUPPORTED_FEATURES] == (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    # Turn off fan mode
    await common.async_set_fan_mode(hass, FAN_OFF)
    await hass.async_block_till_done()

    assert auth.method == "post"
    assert auth.url == DEVICE_COMMAND
    assert auth.json == {
        "command": "sdm.devices.commands.Fan.SetTimer",
        "params": {"timerMode": "OFF"},
    }

    # Turn on fan mode
    await common.async_set_fan_mode(hass, FAN_ON)
    await hass.async_block_till_done()

    assert auth.method == "post"
    assert auth.url == DEVICE_COMMAND
    assert auth.json == {
        "command": "sdm.devices.commands.Fan.SetTimer",
        "params": {
            "duration": "43200s",
            "timerMode": "ON",
        },
    }