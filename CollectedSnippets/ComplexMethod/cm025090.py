async def test_track_template_result_refresh_cancel(hass: HomeAssistant) -> None:
    """Test cancelling and refreshing result."""
    template_refresh = Template("{{states.switch.test.state == 'on' and now() }}", hass)

    refresh_runs = []

    @ha.callback
    def refresh_listener(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        refresh_runs.append(updates.pop().result)

    info = async_track_template_result(
        hass, [TrackTemplate(template_refresh, None)], refresh_listener
    )
    await hass.async_block_till_done()

    hass.states.async_set("switch.test", "off")
    await hass.async_block_till_done()

    assert refresh_runs == [False]

    assert len(refresh_runs) == 1

    info.async_refresh()
    hass.states.async_set("switch.test", "on")
    await hass.async_block_till_done()

    assert len(refresh_runs) == 2
    assert refresh_runs[0] != refresh_runs[1]

    info.async_remove()
    hass.states.async_set("switch.test", "off")
    await hass.async_block_till_done()

    assert len(refresh_runs) == 2

    template_refresh = Template("{{ value }}", hass)
    refresh_runs = []

    info = async_track_template_result(
        hass,
        [TrackTemplate(template_refresh, {"value": "duck"})],
        refresh_listener,
    )
    await hass.async_block_till_done()
    info.async_refresh()
    await hass.async_block_till_done()

    assert refresh_runs == ["duck"]

    info.async_refresh()
    await hass.async_block_till_done()
    assert refresh_runs == ["duck"]