async def test_track_two_templates_with_different_rate_limits(
    hass: HomeAssistant,
) -> None:
    """Test two templates with different rate limits."""
    template_one = Template("{{ (states | count) + 0 }}", hass)
    template_five = Template("{{ states | count }}", hass)

    refresh_runs = {
        template_one: [],
        template_five: [],
    }

    @ha.callback
    def refresh_listener(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        for update in updates:
            refresh_runs[update.template].append(update.result)

    info = async_track_template_result(
        hass,
        [
            TrackTemplate(template_one, None, 0.1),
            TrackTemplate(template_five, None, 5),
        ],
        refresh_listener,
    )

    await hass.async_block_till_done()
    info.async_refresh()
    await hass.async_block_till_done()

    assert refresh_runs[template_one] == [0]
    assert refresh_runs[template_five] == [0]
    hass.states.async_set("sensor.one", "any")
    await hass.async_block_till_done()
    assert refresh_runs[template_one] == [0]
    assert refresh_runs[template_five] == [0]
    info.async_refresh()
    assert refresh_runs[template_one] == [0, 1]
    assert refresh_runs[template_five] == [0, 1]
    hass.states.async_set("sensor.two", "any")
    await hass.async_block_till_done()
    assert refresh_runs[template_one] == [0, 1]
    assert refresh_runs[template_five] == [0, 1]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125 * 1)
    with patch(
        "homeassistant.helpers.ratelimit.time.time", return_value=next_time.timestamp()
    ):
        async_fire_time_changed(hass, next_time)
        await hass.async_block_till_done()
    await hass.async_block_till_done()
    assert refresh_runs[template_one] == [0, 1, 2]
    assert refresh_runs[template_five] == [0, 1]
    hass.states.async_set("sensor.three", "any")
    await hass.async_block_till_done()
    assert refresh_runs[template_one] == [0, 1, 2]
    assert refresh_runs[template_five] == [0, 1]
    hass.states.async_set("sensor.four", "any")
    await hass.async_block_till_done()
    assert refresh_runs[template_one] == [0, 1, 2]
    assert refresh_runs[template_five] == [0, 1]
    hass.states.async_set("sensor.five", "any")
    await hass.async_block_till_done()
    assert refresh_runs[template_one] == [0, 1, 2]
    assert refresh_runs[template_five] == [0, 1]
    info.async_remove()