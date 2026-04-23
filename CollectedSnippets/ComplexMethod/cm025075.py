async def test_track_template_result_super_template_initially_false(
    hass: HomeAssistant,
) -> None:
    """Test tracking template with super template listening to same entity."""
    specific_runs = []
    specific_runs_availability = []
    wildcard_runs = []
    wildcard_runs_availability = []
    wildercard_runs = []
    wildercard_runs_availability = []

    template_availability = Template("{{ is_number(states('sensor.test')) }}", hass)
    template_condition = Template("{{states.sensor.test.state}}", hass)
    template_condition_var = Template(
        "{{(states.sensor.test.state|int) + test }}", hass
    )

    # Make the super template initially false
    hass.states.async_set("sensor.test", "unavailable")
    await hass.async_block_till_done()

    def specific_run_callback(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        for track_result in updates:
            if track_result.template is template_condition:
                specific_runs.append(int(track_result.result))
            elif track_result.template is template_availability:
                specific_runs_availability.append(track_result.result)

    async_track_template_result(
        hass,
        [
            TrackTemplate(template_availability, None),
            TrackTemplate(template_condition, None),
        ],
        specific_run_callback,
        has_super_template=True,
    )

    @ha.callback
    def wildcard_run_callback(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        for track_result in updates:
            if track_result.template is template_condition:
                wildcard_runs.append(
                    (int(track_result.last_result or 0), int(track_result.result))
                )
            elif track_result.template is template_availability:
                wildcard_runs_availability.append(track_result.result)

    async_track_template_result(
        hass,
        [
            TrackTemplate(template_availability, None),
            TrackTemplate(template_condition, None),
        ],
        wildcard_run_callback,
        has_super_template=True,
    )

    async def wildercard_run_callback(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        for track_result in updates:
            if track_result.template is template_condition_var:
                wildercard_runs.append(
                    (int(track_result.last_result or 0), int(track_result.result))
                )
            elif track_result.template is template_availability:
                wildercard_runs_availability.append(track_result.result)

    async_track_template_result(
        hass,
        [
            TrackTemplate(template_availability, None),
            TrackTemplate(template_condition_var, {"test": 5}),
        ],
        wildercard_run_callback,
        has_super_template=True,
    )
    await hass.async_block_till_done()

    assert specific_runs_availability == []
    assert wildcard_runs_availability == []
    assert wildercard_runs_availability == []
    assert specific_runs == []
    assert wildcard_runs == []
    assert wildercard_runs == []

    hass.states.async_set("sensor.test", 5)
    await hass.async_block_till_done()

    assert specific_runs_availability == [True]
    assert wildcard_runs_availability == [True]
    assert wildercard_runs_availability == [True]
    assert specific_runs == [5]
    assert wildcard_runs == [(0, 5)]
    assert wildercard_runs == [(0, 10)]

    hass.states.async_set("sensor.test", "unknown")
    await hass.async_block_till_done()

    assert specific_runs_availability == [True, False]
    assert wildcard_runs_availability == [True, False]
    assert wildercard_runs_availability == [True, False]

    hass.states.async_set("sensor.test", 30)
    await hass.async_block_till_done()

    assert specific_runs_availability == [True, False, True]
    assert wildcard_runs_availability == [True, False, True]
    assert wildercard_runs_availability == [True, False, True]

    assert specific_runs == [5, 30]
    assert wildcard_runs == [(0, 5), (5, 30)]
    assert wildercard_runs == [(0, 10), (10, 35)]

    hass.states.async_set("sensor.test", "other")
    await hass.async_block_till_done()

    hass.states.async_set("sensor.test", 30)
    await hass.async_block_till_done()

    assert len(specific_runs) == 2
    assert len(wildcard_runs) == 2
    assert len(wildercard_runs) == 2
    assert len(specific_runs_availability) == 5
    assert len(wildcard_runs_availability) == 5
    assert len(wildercard_runs_availability) == 5

    hass.states.async_set("sensor.test", 30)
    await hass.async_block_till_done()

    assert len(specific_runs) == 2
    assert len(wildcard_runs) == 2
    assert len(wildercard_runs) == 2
    assert len(specific_runs_availability) == 5
    assert len(wildcard_runs_availability) == 5
    assert len(wildercard_runs_availability) == 5

    hass.states.async_set("sensor.test", 31)
    await hass.async_block_till_done()

    assert len(specific_runs) == 3
    assert len(wildcard_runs) == 3
    assert len(wildercard_runs) == 3
    assert len(specific_runs_availability) == 5
    assert len(wildcard_runs_availability) == 5
    assert len(wildercard_runs_availability) == 5