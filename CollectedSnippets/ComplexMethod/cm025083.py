async def test_track_template_result_transient_errors(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test tracking template with transient errors in the template."""
    hass.states.async_set("sensor.error", "unknown")
    template_that_raises_sometimes = Template(
        "{{ states('sensor.error') | float }}", hass
    )

    sometimes_error_runs = []

    @ha.callback
    def sometimes_error_listener(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        track_result = updates.pop()
        sometimes_error_runs.append(
            (
                event,
                track_result.template,
                track_result.last_result,
                track_result.result,
            )
        )

    info = async_track_template_result(
        hass,
        [TrackTemplate(template_that_raises_sometimes, None)],
        sometimes_error_listener,
    )
    await hass.async_block_till_done()

    assert sometimes_error_runs == []
    assert "ValueError" in caplog.text
    assert "ValueError" in repr(info)
    caplog.clear()

    hass.states.async_set("sensor.error", "unavailable")
    await hass.async_block_till_done()
    assert len(sometimes_error_runs) == 1
    assert isinstance(sometimes_error_runs[0][3], TemplateError)
    sometimes_error_runs.clear()
    assert "ValueError" in repr(info)

    hass.states.async_set("sensor.error", "4")
    await hass.async_block_till_done()
    assert len(sometimes_error_runs) == 1
    assert sometimes_error_runs[0][3] == 4.0
    sometimes_error_runs.clear()
    assert "ValueError" not in repr(info)