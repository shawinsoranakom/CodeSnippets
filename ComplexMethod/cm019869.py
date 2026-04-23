async def test_template(hass: HomeAssistant) -> None:
    """Test a configuration using a complex template."""
    config = CONFIG_FAN[DOMAIN][CONF_ENTITIES]
    assert await async_setup_component(
        hass, FAN_DOMAIN, {FAN_DOMAIN: {"platform": "demo"}}
    )
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await async_setup_component(hass, DOMAIN, CONFIG_FAN) is True
    await hass.async_block_till_done()
    await emulated_kasa.validate_configs(hass, config)

    # Turn all devices on to known state
    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_FAN}, blocking=True
    )
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: ENTITY_FAN, ATTR_PERCENTAGE: 33},
        blocking=True,
    )
    await hass.async_block_till_done()

    fan = hass.states.get(ENTITY_FAN)
    assert fan.state == STATE_ON

    # Fan low:
    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_FAN_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, ENTITY_FAN_SPEED_LOW)

    # Fan High:
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: ENTITY_FAN, ATTR_PERCENTAGE: 100},
        blocking=True,
    )
    await hass.async_block_till_done()
    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_FAN_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, ENTITY_FAN_SPEED_HIGH)

    # Fan off:
    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_FAN}, blocking=True
    )
    await hass.async_block_till_done()
    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_FAN_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 0)