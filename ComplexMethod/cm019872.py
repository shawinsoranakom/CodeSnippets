async def test_multiple_devices(hass: HomeAssistant) -> None:
    """Test that devices are reported correctly."""
    config = CONFIG[DOMAIN][CONF_ENTITIES]
    assert await async_setup_component(
        hass, SWITCH_DOMAIN, {SWITCH_DOMAIN: {"platform": "demo"}}
    )
    assert await async_setup_component(
        hass, LIGHT_DOMAIN, {LIGHT_DOMAIN: {"platform": "demo"}}
    )
    assert await async_setup_component(
        hass, FAN_DOMAIN, {FAN_DOMAIN: {"platform": "demo"}}
    )
    assert await async_setup_component(
        hass,
        SENSOR_DOMAIN,
        {SENSOR_DOMAIN: {"platform": "demo"}},
    )
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await emulated_kasa.async_setup(hass, CONFIG) is True
    await hass.async_block_till_done()
    await emulated_kasa.validate_configs(hass, config)

    # Turn all devices on to known state
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )
    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_LIGHT}, blocking=True
    )
    hass.states.async_set(ENTITY_SENSOR, 35)
    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_FAN}, blocking=True
    )
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: ENTITY_FAN, ATTR_PERCENTAGE: 66},
        blocking=True,
    )
    await hass.async_block_till_done()

    # All of them should now be on
    switch = hass.states.get(ENTITY_SWITCH)
    assert switch.state == STATE_ON
    light = hass.states.get(ENTITY_LIGHT)
    assert light.state == STATE_ON
    sensor = hass.states.get(ENTITY_SENSOR)
    assert sensor.state == "35"
    fan = hass.states.get(ENTITY_FAN)
    assert fan.state == STATE_ON

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    # switch
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SWITCH_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, ENTITY_SWITCH_POWER)

    # light
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_LIGHT_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 35)

    # fan
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_FAN_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, ENTITY_FAN_SPEED_MED)

    # No more devices
    assert next(plug_it, None) is None