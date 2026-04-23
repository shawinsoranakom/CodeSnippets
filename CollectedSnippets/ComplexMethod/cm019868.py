async def test_float(hass: HomeAssistant) -> None:
    """Test a configuration using a simple float."""
    config = CONFIG_SWITCH[DOMAIN][CONF_ENTITIES]
    assert await async_setup_component(
        hass,
        SWITCH_DOMAIN,
        {SWITCH_DOMAIN: {"platform": "demo"}},
    )
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await async_setup_component(hass, DOMAIN, CONFIG_SWITCH) is True
    await hass.async_block_till_done()
    await emulated_kasa.validate_configs(hass, config)

    # Turn switch on
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )
    await hass.async_block_till_done()

    switch = hass.states.get(ENTITY_SWITCH)
    assert switch.state == STATE_ON

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()

    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SWITCH_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, ENTITY_SWITCH_POWER)

    # Turn off
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )
    await hass.async_block_till_done()

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SWITCH_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 0)