async def test_thermostat_missing_temperature_trait(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    create_device: CreateDevice,
) -> None:
    """Test a thermostat missing many thermostat traits in api response."""
    create_device.create(
        {
            "sdm.devices.traits.ThermostatHvac": {"status": "OFF"},
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
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    assert thermostat.attributes[ATTR_CURRENT_TEMPERATURE] is None
    assert set(thermostat.attributes[ATTR_HVAC_MODES]) == {
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
        HVACMode.OFF,
    }
    assert thermostat.attributes[ATTR_TEMPERATURE] is None
    assert thermostat.attributes[ATTR_TARGET_TEMP_LOW] is None
    assert thermostat.attributes[ATTR_TARGET_TEMP_HIGH] is None
    assert ATTR_PRESET_MODE not in thermostat.attributes
    assert ATTR_PRESET_MODES not in thermostat.attributes
    assert ATTR_FAN_MODE not in thermostat.attributes
    assert ATTR_FAN_MODES not in thermostat.attributes

    with pytest.raises(HomeAssistantError) as e_info:
        await common.async_set_temperature(hass, temperature=24.0)
    await hass.async_block_till_done()
    assert "temperature" in str(e_info)
    assert "climate.my_thermostat" in str(e_info)
    assert "24.0" in str(e_info)
    assert thermostat.attributes[ATTR_TEMPERATURE] is None