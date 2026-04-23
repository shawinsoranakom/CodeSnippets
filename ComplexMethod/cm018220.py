async def test_non_json_message(
    hass: HomeAssistant, websocket_client, caplog: pytest.LogCaptureFixture
) -> None:
    """Test trying to serialize non JSON objects."""
    bad_data = object()
    hass.states.async_set("test_domain.entity", "testing", {"bad": bad_data})
    await websocket_client.send_json({"id": 5, "type": "get_states"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == []
    assert "Unable to serialize to JSON. Bad data found" in caplog.text
    assert "State: test_domain.entity" in caplog.text
    assert "bad=<object" in caplog.text