async def test_thermostat_hvac_mode_failure(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    auth: FakeAuth,
    create_device: CreateDevice,
) -> None:
    """Test setting an hvac_mode that is not supported."""
    create_device.create(
        {
            "sdm.devices.traits.ThermostatHvac": {"status": "OFF"},
            "sdm.devices.traits.ThermostatMode": {
                "availableModes": ["HEAT", "COOL", "HEATCOOL", "OFF"],
                "mode": "COOL",
            },
            "sdm.devices.traits.ThermostatTemperatureSetpoint": {
                "coolCelsius": 25.0,
            },
            "sdm.devices.traits.Fan": {
                "timerMode": "OFF",
                "timerTimeout": "2019-05-10T03:22:54Z",
            },
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
    assert thermostat.state == HVACMode.COOL
    assert thermostat.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE

    auth.responses = [aiohttp.web.Response(status=HTTPStatus.BAD_REQUEST)]
    with pytest.raises(HomeAssistantError) as e_info:
        await common.async_set_hvac_mode(hass, HVACMode.HEAT)
    assert "HVAC mode" in str(e_info)
    assert "climate.my_thermostat" in str(e_info)
    assert HVACMode.HEAT in str(e_info)

    auth.responses = [aiohttp.web.Response(status=HTTPStatus.BAD_REQUEST)]
    with pytest.raises(HomeAssistantError) as e_info:
        await common.async_set_temperature(hass, temperature=25.0)
    assert "temperature" in str(e_info)
    assert "climate.my_thermostat" in str(e_info)
    assert "25.0" in str(e_info)

    auth.responses = [aiohttp.web.Response(status=HTTPStatus.BAD_REQUEST)]
    with pytest.raises(HomeAssistantError) as e_info:
        await common.async_set_fan_mode(hass, FAN_ON)
    assert "fan mode" in str(e_info)
    assert "climate.my_thermostat" in str(e_info)
    assert FAN_ON in str(e_info)

    auth.responses = [aiohttp.web.Response(status=HTTPStatus.BAD_REQUEST)]
    with pytest.raises(HomeAssistantError) as e_info:
        await common.async_set_preset_mode(hass, PRESET_ECO)
    assert "preset mode" in str(e_info)
    assert "climate.my_thermostat" in str(e_info)
    assert PRESET_ECO in str(e_info)