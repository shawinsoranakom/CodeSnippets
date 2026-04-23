async def test_track_template_result_super_template_2(
    hass: HomeAssistant, availability_template: str
) -> None:
    """Test tracking template with super template listening to different entities."""
    specific_runs = []
    specific_runs_availability = []
    wildcard_runs = []
    wildcard_runs_availability = []
    wildercard_runs = []
    wildercard_runs_availability = []

    template_availability = Template(availability_template, hass)
    template_condition = Template("{{states.sensor.test.state}}", hass)
    template_condition_var = Template(
        "{{(states.sensor.test.state|int) + test }}", hass
    )

    def _super_template_as_boolean(result):
        if isinstance(result, TemplateError):
            return True

        return result_as_boolean(result)

    def specific_run_callback(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        for track_result in updates:
            if track_result.template is template_condition:
                specific_runs.append(int(track_result.result))
            elif track_result.template is template_availability:
                specific_runs_availability.append(
                    _super_template_as_boolean(track_result.result)
                )

    info = async_track_template_result(
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
                wildcard_runs_availability.append(
                    _super_template_as_boolean(track_result.result)
                )

    info2 = async_track_template_result(
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
                wildercard_runs_availability.append(
                    _super_template_as_boolean(track_result.result)
                )

    info3 = async_track_template_result(
        hass,
        [
            TrackTemplate(template_availability, None),
            TrackTemplate(template_condition_var, {"test": 5}),
        ],
        wildercard_run_callback,
        has_super_template=True,
    )
    await hass.async_block_till_done()

    hass.states.async_set("sensor.test2", "unavailable")
    await hass.async_block_till_done()

    assert specific_runs_availability == [False]
    assert wildcard_runs_availability == [False]
    assert wildercard_runs_availability == [False]
    assert specific_runs == []
    assert wildcard_runs == []
    assert wildercard_runs == []

    hass.states.async_set("sensor.test", 5)
    hass.states.async_set("sensor.test2", "available")
    await hass.async_block_till_done()

    assert specific_runs_availability == [False, True]
    assert wildcard_runs_availability == [False, True]
    assert wildercard_runs_availability == [False, True]
    assert specific_runs == [5]
    assert wildcard_runs == [(0, 5)]
    assert wildercard_runs == [(0, 10)]

    hass.states.async_set("sensor.test2", "unknown")
    await hass.async_block_till_done()

    assert specific_runs_availability == [False, True]
    assert wildcard_runs_availability == [False, True]
    assert wildercard_runs_availability == [False, True]

    hass.states.async_set("sensor.test2", "available")
    hass.states.async_set("sensor.test", 30)
    await hass.async_block_till_done()

    assert specific_runs_availability == [False, True]
    assert wildcard_runs_availability == [False, True]
    assert wildercard_runs_availability == [False, True]
    assert specific_runs == [5, 30]
    assert wildcard_runs == [(0, 5), (5, 30)]
    assert wildercard_runs == [(0, 10), (10, 35)]

    info.async_remove()
    info2.async_remove()
    info3.async_remove()