async def test_track_template_rate_limit_super(hass: HomeAssistant) -> None:
    """Test template rate limit with super template."""
    template_availability = Template(
        "{{ states('sensor.one') != 'unavailable' }}", hass
    )
    template_refresh = Template("{{ states | count }}", hass)

    availability_runs = []
    refresh_runs = []

    @ha.callback
    def refresh_listener(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        for track_result in updates:
            if track_result.template is template_refresh:
                refresh_runs.append(track_result.result)
            elif track_result.template is template_availability:
                availability_runs.append(track_result.result)

    info = async_track_template_result(
        hass,
        [
            TrackTemplate(template_availability, None),
            TrackTemplate(template_refresh, None, 0.1),
        ],
        refresh_listener,
        has_super_template=True,
    )
    await hass.async_block_till_done()
    info.async_refresh()
    await hass.async_block_till_done()

    assert refresh_runs == [0]
    hass.states.async_set("sensor.one", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0]
    info.async_refresh()
    assert refresh_runs == [0, 1]
    hass.states.async_set("sensor.two", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1]
    hass.states.async_set("sensor.one", "unavailable")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125)
    with patch(
        "homeassistant.helpers.ratelimit.time.time", return_value=next_time.timestamp()
    ):
        async_fire_time_changed(hass, next_time)
        await hass.async_block_till_done()
    assert refresh_runs == [0, 1]
    hass.states.async_set("sensor.three", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1]
    hass.states.async_set("sensor.four", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1]
    # The super template renders as true -> trigger rerendering of all templates
    hass.states.async_set("sensor.one", "available")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1, 4]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125 * 2)
    with patch(
        "homeassistant.helpers.ratelimit.time.time", return_value=next_time.timestamp()
    ):
        async_fire_time_changed(hass, next_time)
        await hass.async_block_till_done()
    assert refresh_runs == [0, 1, 4]
    hass.states.async_set("sensor.five", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1, 4]

    info.async_remove()