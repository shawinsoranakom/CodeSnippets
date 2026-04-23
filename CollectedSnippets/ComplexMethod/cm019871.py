async def test_sensor_state(hass: HomeAssistant) -> None:
    """Test a configuration using a sensor in a template."""
    config = CONFIG_SENSOR[DOMAIN][CONF_ENTITIES]
    assert await async_setup_component(
        hass,
        SENSOR_DOMAIN,
        {SENSOR_DOMAIN: {"platform": "demo"}},
    )
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        assert await async_setup_component(hass, DOMAIN, CONFIG_SENSOR) is True
    await hass.async_block_till_done()
    await emulated_kasa.validate_configs(hass, config)

    hass.states.async_set(ENTITY_SENSOR, 35)

    sensor = hass.states.get(ENTITY_SENSOR)
    assert sensor.state == "35"

    # sensor
    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SENSOR_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 35)

    # change power sensor
    hass.states.async_set(ENTITY_SENSOR, 40)

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SENSOR_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 40)

    # report 0 if device is off
    hass.states.async_set(ENTITY_SENSOR, 0)

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    assert nested_value(plug, "system", "get_sysinfo", "alias") == ENTITY_SENSOR_NAME
    power = nested_value(plug, "emeter", "get_realtime", "power")
    assert math.isclose(power, 0)