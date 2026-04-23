async def test_thermostat_missing_mode_traits(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    create_device: CreateDevice,
) -> None:
    """Test a thermostat missing many thermostat traits in api response."""
    create_device.create(
        {
            "sdm.devices.traits.ThermostatHvac": {"status": "OFF"},
        }
    )
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    thermostat = hass.states.get("climate.my_thermostat")
    assert thermostat is not None
    assert thermostat.state == HVACMode.OFF
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.OFF
    assert thermostat.attributes[ATTR_CURRENT_TEMPERATURE] is None
    assert set(thermostat.attributes[ATTR_HVAC_MODES]) == set()
    assert ATTR_TEMPERATURE not in thermostat.attributes
    assert ATTR_TARGET_TEMP_LOW not in thermostat.attributes
    assert ATTR_TARGET_TEMP_HIGH not in thermostat.attributes
    assert ATTR_PRESET_MODE not in thermostat.attributes
    assert ATTR_PRESET_MODES not in thermostat.attributes
    assert ATTR_FAN_MODE not in thermostat.attributes
    assert ATTR_FAN_MODES not in thermostat.attributes

    await common.async_set_temperature(hass, temperature=24.0)
    await hass.async_block_till_done()
    assert ATTR_TEMPERATURE not in thermostat.attributes

    await common.async_set_preset_mode(hass, PRESET_ECO)
    await hass.async_block_till_done()
    assert ATTR_PRESET_MODE not in thermostat.attributes