async def test_reloadable(hass: HomeAssistant) -> None:
    """Test that we can reload."""
    hass.states.async_set("sensor.test_sensor", "mytest")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.top_level_state").state == "unknown + 2"
    assert hass.states.get("binary_sensor.top_level_state").state == "off"

    hass.bus.async_fire("event_1", {"source": "init"})
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 5
    assert hass.states.get("sensor.state").state == "mytest"
    assert hass.states.get("sensor.top_level").state == "init"
    await hass.async_block_till_done()
    assert hass.states.get("sensor.top_level_state").state == "init + 2"
    assert hass.states.get("binary_sensor.top_level_state").state == "on"

    await async_yaml_patch_helper(hass, "sensor_configuration.yaml")
    assert len(hass.states.async_all()) == 4

    hass.bus.async_fire("event_2", {"source": "reload"})
    await hass.async_block_till_done()
    assert hass.states.get("sensor.state") is None
    assert hass.states.get("sensor.top_level") is None
    assert hass.states.get("sensor.watching_tv_in_master_bedroom").state == "off"
    assert float(hass.states.get("sensor.combined_sensor_energy_usage").state) == 0
    assert hass.states.get("sensor.top_level_2").state == "reload"