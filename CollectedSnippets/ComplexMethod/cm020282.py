async def test_thermostat_set_hvac_mode(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    auth: FakeAuth,
    create_device: CreateDevice,
    create_event: CreateEvent,
) -> None:
    """Test a thermostat changing hvac modes."""
    create_device.create(
        {
            "sdm.devices.traits.ThermostatHvac": {"status": "OFF"},
            "sdm.devices.traits.ThermostatMode": {
                "availableModes": ["HEAT", "COOL", "HEATCOOL", "OFF"],
                "mode": "OFF",
            },
        }
    )
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.OFF
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF

    await common.async_set_hvac_mode(hass, HVACMode.HEAT)
    await hass.async_block_till_done()

    assert auth.method == "post"
    assert auth.url == DEVICE_COMMAND
    assert auth.json == {
        "command": "sdm.devices.commands.ThermostatMode.SetMode",
        "params": {"mode": "HEAT"},
    }

    # Local state does not reflect the update
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.OFF
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF

    # Simulate pubsub message when mode changes
    await create_event(
        {
            "sdm.devices.traits.ThermostatMode": {
                "availableModes": ["HEAT", "COOL", "HEATCOOL", "OFF"],
                "mode": "HEAT",
            },
        }
    )

    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.HEAT
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE

    # Simulate pubsub message when the thermostat starts heating
    await create_event(
        {
            "sdm.devices.traits.ThermostatHvac": {
                "status": "HEATING",
            },
        }
    )

    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.HEAT
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.HEATING