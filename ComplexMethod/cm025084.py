async def test_track_template_rate_limit(hass: HomeAssistant) -> None:
    """Test template rate limit."""
    template_refresh = Template("{{ states | count }}", hass)

    refresh_runs = []

    @ha.callback
    def refresh_listener(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        refresh_runs.append(updates.pop().result)

    info = async_track_template_result(
        hass,
        [TrackTemplate(template_refresh, None, 0.1)],
        refresh_listener,
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
    hass.states.async_set("sensor.TWO", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125)
    with patch(
        "homeassistant.helpers.ratelimit.time.time", return_value=next_time.timestamp()
    ):
        async_fire_time_changed(hass, next_time)
        await hass.async_block_till_done()
    assert refresh_runs == [0, 1, 2]
    hass.states.async_set("sensor.three", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1, 2]
    hass.states.async_set("sensor.fOuR", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1, 2]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125 * 2)
    with patch(
        "homeassistant.helpers.ratelimit.time.time", return_value=next_time.timestamp()
    ):
        async_fire_time_changed(hass, next_time)
        await hass.async_block_till_done()
    assert refresh_runs == [0, 1, 2, 4]
    hass.states.async_set("sensor.five", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1, 2, 4]

    info.async_remove()