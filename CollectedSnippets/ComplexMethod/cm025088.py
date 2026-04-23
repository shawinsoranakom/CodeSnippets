async def test_track_template_rate_limit_suppress_listener(hass: HomeAssistant) -> None:
    """Test template rate limit will suppress the listener during the rate limit."""
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

    assert info.listeners == {
        "all": True,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    await hass.async_block_till_done()

    assert refresh_runs == [0]
    hass.states.async_set("sensor.oNe", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0]
    info.async_refresh()
    assert refresh_runs == [0, 1]
    hass.states.async_set("sensor.two", "any")
    await hass.async_block_till_done()
    # Should be suppressed during the rate limit
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    assert refresh_runs == [0, 1]
    next_time = dt_util.utcnow() + timedelta(seconds=0.125)
    with patch(
        "homeassistant.helpers.ratelimit.time.time", return_value=next_time.timestamp()
    ):
        async_fire_time_changed(hass, next_time)
        await hass.async_block_till_done()
    # Rate limit released and the all listener returns
    assert info.listeners == {
        "all": True,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    assert refresh_runs == [0, 1, 2]
    hass.states.async_set("sensor.Three", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1, 2]
    hass.states.async_set("sensor.four", "any")
    await hass.async_block_till_done()
    assert refresh_runs == [0, 1, 2]
    # Rate limit hit and the all listener is shut off
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    next_time = dt_util.utcnow() + timedelta(seconds=0.125 * 2)
    with patch(
        "homeassistant.helpers.ratelimit.time.time", return_value=next_time.timestamp()
    ):
        async_fire_time_changed(hass, next_time)
        await hass.async_block_till_done()
    # Rate limit released and the all listener returns
    assert info.listeners == {
        "all": True,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    assert refresh_runs == [0, 1, 2, 4]
    hass.states.async_set("sensor.Five", "any")
    await hass.async_block_till_done()
    # Rate limit hit and the all listener is shut off
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": set(),
        "time": False,
    }
    assert refresh_runs == [0, 1, 2, 4]

    info.async_remove()