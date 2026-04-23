async def test_render_template_error_in_template_code(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    caplog: pytest.LogCaptureFixture,
    template: str,
    expected_events_1: list[dict[str, str]],
    expected_events_2: list[dict[str, str]],
) -> None:
    """Test a template that will throw in template.py.

    In this test report_errors is enabled.
    """
    await websocket_client.send_json_auto_id(
        {
            "type": "render_template",
            "template": template,
            "report_errors": True,
        }
    )

    for expected_event in expected_events_1:
        msg = await websocket_client.receive_json()
        for key, value in expected_event.items():
            assert msg[key] == value

    hass.states.async_set("sensor.foo", "2")

    for expected_event in expected_events_2:
        msg = await websocket_client.receive_json()
        for key, value in expected_event.items():
            assert msg[key] == value

    assert "Template variable error" not in caplog.text
    assert "Template variable warning" not in caplog.text
    assert "TemplateError" not in caplog.text