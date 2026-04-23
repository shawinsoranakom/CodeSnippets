async def test_render_template_with_delayed_error(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a template with an error that only happens after a state change.

    In this test report_errors is enabled.
    """
    caplog.set_level(logging.INFO)
    hass.states.async_set("sensor.test", "on")
    await hass.async_block_till_done()

    template_str = """
{% if states.sensor.test.state %}
   on
{% else %}
   {{ explode + 1 }}
{% endif %}
    """

    await websocket_client.send_json_auto_id(
        {
            "type": "render_template",
            "template": template_str,
            "report_errors": True,
        }
    )
    await hass.async_block_till_done()

    msg = await websocket_client.receive_json()
    subscription = msg["id"]
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    hass.states.async_remove("sensor.test")
    await hass.async_block_till_done()

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    event = msg["event"]
    assert event == {
        "result": "on",
        "listeners": {
            "all": False,
            "domains": [],
            "entities": ["sensor.test"],
            "time": False,
        },
    }

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    event = msg["event"]
    assert event["error"] == "'None' has no attribute 'state'"

    msg = await websocket_client.receive_json()
    assert msg["id"] == subscription
    assert msg["type"] == "event"
    event = msg["event"]
    assert event == {
        "error": "UndefinedError: 'explode' is undefined",
        "level": "ERROR",
    }

    assert "Template variable error" not in caplog.text
    assert "Template variable warning" not in caplog.text
    assert "TemplateError" not in caplog.text