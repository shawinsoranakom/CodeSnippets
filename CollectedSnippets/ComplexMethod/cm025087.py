async def test_track_template_rate_limit_super_3(hass: HomeAssistant) -> None:
    """Test template with rate limited super template."""
    # Somewhat forced example of a rate limited template
    template_availability = Template("{{ states | count % 2 == 1 }}", hass)
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
            TrackTemplate(template_availability, None, 0.1),
            TrackTemplate(template_refresh, None),
        ],
        refresh_listener,
        has_super_template=True,
    )
    await hass.async_block_till_done()
    info.async_refresh()
    await hass.async_block_till_done()

    assert refresh_runs == []
    hass.states.async_set("sensor.ONE", "any")
    await hass.async_block_till_done()
    assert refresh_runs == []
    info.async_refresh()
    assert refresh_runs == [1]
    hass.states.async_set("sensor.two", "any")
    await hass.async_block_till_done()
    # The super template is rate limited so stuck at `True`
    assert refresh_runs == [1, 2]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125)
    with patch(
        "homeassistant.helpers.ratelimit.time.time", return_value=next_time.timestamp()
    ):
        async_fire_time_changed(hass, next_time)
        await hass.async_block_till_done()
    assert refresh_runs == [1, 2]
    hass.states.async_set("sensor.three", "any")
    await hass.async_block_till_done()
    # The super template is rate limited so stuck at `False`
    assert refresh_runs == [1, 2]
    hass.states.async_set("sensor.four", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [1, 2]
    hass.states.async_set("sensor.FIVE", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [1, 2]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125 * 2)
    with patch(
        "homeassistant.helpers.ratelimit.time.time", return_value=next_time.timestamp()
    ):
        async_fire_time_changed(hass, next_time)
        await hass.async_block_till_done()
    assert refresh_runs == [1, 2, 5]
    hass.states.async_set("sensor.six", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [1, 2, 5, 6]
    hass.states.async_set("sensor.seven", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [1, 2, 5, 6, 7]

    info.async_remove()