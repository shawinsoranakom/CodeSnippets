async def test_track_template_result_errors(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test tracking template with errors in the template."""
    template_syntax_error = Template("{{states.switch", hass)

    template_not_exist = Template("{{states.switch.not_exist.state }}", hass)

    syntax_error_runs = []
    not_exist_runs = []

    @ha.callback
    def syntax_error_listener(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        track_result = updates.pop()
        syntax_error_runs.append(
            (
                event,
                track_result.template,
                track_result.last_result,
                track_result.result,
            )
        )

    async_track_template_result(
        hass, [TrackTemplate(template_syntax_error, None)], syntax_error_listener
    )
    await hass.async_block_till_done()

    assert len(syntax_error_runs) == 0
    assert "TemplateSyntaxError" in caplog.text

    @ha.callback
    def not_exist_runs_error_listener(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        template_track = updates.pop()
        not_exist_runs.append(
            (
                event,
                template_track.template,
                template_track.last_result,
                template_track.result,
            )
        )

    async_track_template_result(
        hass,
        [TrackTemplate(template_not_exist, None)],
        not_exist_runs_error_listener,
    )
    await hass.async_block_till_done()

    assert len(syntax_error_runs) == 0
    assert len(not_exist_runs) == 0

    hass.states.async_set("switch.not_exist", "off")
    await hass.async_block_till_done()

    assert len(not_exist_runs) == 1
    assert not_exist_runs[0][0].data.get("entity_id") == "switch.not_exist"
    assert not_exist_runs[0][1] == template_not_exist
    assert not_exist_runs[0][2] is None
    assert not_exist_runs[0][3] == "off"

    hass.states.async_set("switch.not_exist", "on")
    await hass.async_block_till_done()

    assert len(syntax_error_runs) == 0
    assert len(not_exist_runs) == 2
    assert not_exist_runs[1][0].data.get("entity_id") == "switch.not_exist"
    assert not_exist_runs[1][1] == template_not_exist
    assert not_exist_runs[1][2] == "off"
    assert not_exist_runs[1][3] == "on"

    with patch.object(Template, "async_render") as render:
        render.side_effect = TemplateError(jinja2.TemplateError())

        hass.states.async_set("switch.not_exist", "off")
        await hass.async_block_till_done()

        assert len(not_exist_runs) == 3
        assert not_exist_runs[2][0].data.get("entity_id") == "switch.not_exist"
        assert not_exist_runs[2][1] == template_not_exist
        assert not_exist_runs[2][2] == "on"
        assert isinstance(not_exist_runs[2][3], TemplateError)