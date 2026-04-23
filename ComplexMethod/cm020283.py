async def test_thermostat_set_eco_preset(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    auth: FakeAuth,
    create_device: CreateDevice,
    create_event: CreateEvent,
) -> None:
    """Test a thermostat put into eco mode."""
    create_device.create(
        {
            "sdm.devices.traits.ThermostatHvac": {"status": "OFF"},
            "sdm.devices.traits.ThermostatEco": {
                "availableModes": ["MANUAL_ECO", "OFF"],
                "mode": "OFF",
                "heatCelsius": 15.0,
                "coolCelsius": 28.0,
            },
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
    assert thermostat.attributes[ATTR_PRESET_MODE] == PRESET_NONE

    # Turn on eco mode
    await common.async_set_preset_mode(hass, PRESET_ECO)
    await hass.async_block_till_done()

    assert auth.method == "post"
    assert auth.url == DEVICE_COMMAND
    assert auth.json == {
        "command": "sdm.devices.commands.ThermostatEco.SetMode",
        "params": {"mode": "MANUAL_ECO"},
    }

    # Local state does not reflect the update
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.OFF
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF
    assert thermostat.attributes[ATTR_PRESET_MODE] == PRESET_NONE

    # Simulate pubsub message when mode changes
    await create_event(
        {
            "sdm.devices.traits.ThermostatEco": {
                "availableModes": ["HEAT", "COOL", "HEATCOOL", "OFF"],
                "mode": "MANUAL_ECO",
                "heatCelsius": 15.0,
                "coolCelsius": 28.0,
            },
        }
    )

    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.OFF
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF
    assert thermostat.attributes[ATTR_PRESET_MODE] == PRESET_ECO

    # Turn off eco mode
    await common.async_set_preset_mode(hass, PRESET_NONE)
    await hass.async_block_till_done()

    assert auth.method == "post"
    assert auth.url == DEVICE_COMMAND
    assert auth.json == {
        "command": "sdm.devices.commands.ThermostatEco.SetMode",
        "params": {"mode": "OFF"},
    }

    # Simulate the mode changing
    await create_event(
        {
            "sdm.devices.traits.ThermostatEco": {
                "availableModes": ["HEAT", "COOL", "HEATCOOL", "OFF"],
                "mode": "OFF",
            },
        }
    )

    auth.method = None
    auth.url = None
    auth.json = None

    # Attempting to set the preset mode when already in that mode will
    # not send any messages to the API (it would otherwise fail)
    await common.async_set_preset_mode(hass, PRESET_NONE)
    await hass.async_block_till_done()

    assert auth.method is None
    assert auth.url is None
    assert auth.json is None