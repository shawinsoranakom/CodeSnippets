async def test_track_template_result(hass: HomeAssistant) -> None:
    """Test tracking template."""
    specific_runs = []
    wildcard_runs = []
    wildercard_runs = []

    template_condition = Template("{{states.sensor.test.state}}", hass)
    template_condition_var = Template(
        "{{(states.sensor.test.state|int) + test }}", hass
    )

    def specific_run_callback(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        track_result = updates.pop()
        specific_runs.append(int(track_result.result))

    async_track_template_result(
        hass, [TrackTemplate(template_condition, None)], specific_run_callback
    )

    @ha.callback
    def wildcard_run_callback(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        track_result = updates.pop()
        wildcard_runs.append(
            (int(track_result.last_result or 0), int(track_result.result))
        )

    async_track_template_result(
        hass, [TrackTemplate(template_condition, None)], wildcard_run_callback
    )

    async def wildercard_run_callback(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        track_result = updates.pop()
        wildercard_runs.append(
            (int(track_result.last_result or 0), int(track_result.result))
        )

    async_track_template_result(
        hass,
        [TrackTemplate(template_condition_var, {"test": 5})],
        wildercard_run_callback,
    )
    await hass.async_block_till_done()

    hass.states.async_set("sensor.test", 5)
    await hass.async_block_till_done()

    assert specific_runs == [5]
    assert wildcard_runs == [(0, 5)]
    assert wildercard_runs == [(0, 10)]

    hass.states.async_set("sensor.test", 30)
    await hass.async_block_till_done()

    assert specific_runs == [5, 30]
    assert wildcard_runs == [(0, 5), (5, 30)]
    assert wildercard_runs == [(0, 10), (10, 35)]

    hass.states.async_set("sensor.test", 30)
    await hass.async_block_till_done()

    assert len(specific_runs) == 2
    assert len(wildcard_runs) == 2
    assert len(wildercard_runs) == 2

    hass.states.async_set("sensor.test", 5)
    await hass.async_block_till_done()

    assert len(specific_runs) == 3
    assert len(wildcard_runs) == 3
    assert len(wildercard_runs) == 3

    hass.states.async_set("sensor.test", 5)
    await hass.async_block_till_done()

    assert len(specific_runs) == 3
    assert len(wildcard_runs) == 3
    assert len(wildercard_runs) == 3

    hass.states.async_set("sensor.test", 20)
    await hass.async_block_till_done()

    assert len(specific_runs) == 4
    assert len(wildcard_runs) == 4
    assert len(wildercard_runs) == 4