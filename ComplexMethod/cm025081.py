async def test_track_template_result_and_conditional_upper_case(
    hass: HomeAssistant,
) -> None:
    """Test tracking template with an and conditional with an upper case template."""
    specific_runs = []
    hass.states.async_set("light.a", "off")
    hass.states.async_set("light.b", "off")
    template_str = '{% if states.light.A.state == "on" and states.light.B.state == "on" %}on{% else %}off{% endif %}'

    template = Template(template_str, hass)

    def specific_run_callback(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        specific_runs.append(updates.pop().result)

    info = async_track_template_result(
        hass, [TrackTemplate(template, None)], specific_run_callback
    )
    await hass.async_block_till_done()
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"light.a"},
        "time": False,
    }

    hass.states.async_set("light.b", "on")
    await hass.async_block_till_done()
    assert len(specific_runs) == 0

    hass.states.async_set("light.a", "on")
    await hass.async_block_till_done()
    assert len(specific_runs) == 1
    assert specific_runs[0] == "on"
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"light.a", "light.b"},
        "time": False,
    }

    hass.states.async_set("light.b", "off")
    await hass.async_block_till_done()
    assert len(specific_runs) == 2
    assert specific_runs[1] == "off"
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"light.a", "light.b"},
        "time": False,
    }

    hass.states.async_set("light.a", "off")
    await hass.async_block_till_done()
    assert len(specific_runs) == 2

    hass.states.async_set("light.b", "on")
    await hass.async_block_till_done()
    assert len(specific_runs) == 2

    hass.states.async_set("light.a", "on")
    await hass.async_block_till_done()
    assert len(specific_runs) == 3
    assert specific_runs[2] == "on"