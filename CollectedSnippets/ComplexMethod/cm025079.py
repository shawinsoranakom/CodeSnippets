async def test_track_template_result_with_group(hass: HomeAssistant) -> None:
    """Test tracking template with a group."""
    hass.states.async_set("sensor.power_1", 0)
    hass.states.async_set("sensor.power_2", 200.2)
    hass.states.async_set("sensor.power_3", 400.4)
    hass.states.async_set("sensor.power_4", 800.8)

    assert await async_setup_component(
        hass,
        "group",
        {"group": {"power_sensors": "sensor.power_1,sensor.power_2,sensor.power_3"}},
    )
    await hass.async_block_till_done()

    assert hass.states.get("group.power_sensors")
    assert hass.states.get("group.power_sensors").state

    specific_runs = []
    template_complex_str = r"""

{{ states.group.power_sensors.attributes.entity_id | expand | map(attribute='state')|map('float')|sum  }}

"""
    template_complex = Template(template_complex_str, hass)

    def specific_run_callback(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        specific_runs.append(updates.pop().result)

    info = async_track_template_result(
        hass, [TrackTemplate(template_complex, None)], specific_run_callback
    )
    await hass.async_block_till_done()

    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {
            "group.power_sensors",
            "sensor.power_1",
            "sensor.power_2",
            "sensor.power_3",
        },
        "time": False,
    }

    hass.states.async_set("sensor.power_1", 100.1)
    await hass.async_block_till_done()
    assert len(specific_runs) == 1

    assert specific_runs[0] == 100.1 + 200.2 + 400.4

    hass.states.async_set("sensor.power_3", 0)
    await hass.async_block_till_done()
    assert len(specific_runs) == 2

    assert specific_runs[1] == 100.1 + 200.2 + 0

    with patch(
        "homeassistant.config.load_yaml_config_file",
        return_value={
            "group": {
                "power_sensors": "sensor.power_1,sensor.power_2,sensor.power_3,sensor.power_4",
            }
        },
    ):
        await hass.services.async_call("group", "reload")
        await hass.async_block_till_done()

    info.async_refresh()
    await hass.async_block_till_done()
    assert specific_runs[-1] == 100.1 + 200.2 + 0 + 800.8