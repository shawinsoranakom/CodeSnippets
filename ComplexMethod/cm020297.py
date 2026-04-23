async def test_thermostat_invalid_set_preset_mode(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    auth: FakeAuth,
    create_device: CreateDevice,
) -> None:
    """Test a thermostat set with an invalid preset mode."""
    create_device.create(
        {
            "sdm.devices.traits.ThermostatHvac": {"status": "OFF"},
            "sdm.devices.traits.ThermostatEco": {
                "availableModes": ["MANUAL_ECO", "OFF"],
                "mode": "OFF",
                "heatCelsius": 15.0,
                "coolCelsius": 28.0,
            },
        }
    )
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.OFF
    assert thermostat.attributes[ATTR_PRESET_MODE] == PRESET_NONE
    assert thermostat.attributes[ATTR_PRESET_MODES] == [PRESET_ECO, PRESET_NONE]

    # Set preset mode that is invalid
    with pytest.raises(ServiceValidationError):
        await common.async_set_preset_mode(hass, PRESET_SLEEP)

    # No RPC sent
    assert auth.method is None

    # Preset is unchanged
    assert thermostat.attributes[ATTR_PRESET_MODE] == PRESET_NONE
    assert thermostat.attributes[ATTR_PRESET_MODES] == [PRESET_ECO, PRESET_NONE]