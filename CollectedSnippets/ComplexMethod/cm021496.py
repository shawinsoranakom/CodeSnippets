async def test_reloadable_multiple_platforms(hass: HomeAssistant) -> None:
    """Test that we can reload."""
    hass.states.async_set("sensor.test_sensor", "mytest")
    await async_setup_component(
        hass,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": DOMAIN,
                "sensors": {
                    "state": {
                        "value_template": "{{ states.sensor.test_sensor.state }}"
                    },
                },
            }
        },
    )
    await hass.async_block_till_done()
    assert hass.states.get("sensor.state").state == "mytest"
    assert hass.states.get("binary_sensor.state").state == "off"
    assert len(hass.states.async_all()) == 3

    await async_yaml_patch_helper(hass, "sensor_configuration.yaml")
    assert len(hass.states.async_all()) == 4
    assert hass.states.get("sensor.state") is None
    assert hass.states.get("sensor.watching_tv_in_master_bedroom").state == "off"
    assert float(hass.states.get("sensor.combined_sensor_energy_usage").state) == 0
    assert hass.states.get("sensor.top_level_2") is not None