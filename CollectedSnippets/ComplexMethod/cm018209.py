async def test_test_condition(
    hass: HomeAssistant, websocket_client: MockHAClientWebSocket
) -> None:
    """Test testing a condition."""
    hass.states.async_set("hello.world", "paulus")

    await websocket_client.send_json_auto_id(
        {
            "type": "test_condition",
            "condition": {
                "condition": "state",
                "entity_id": "hello.world",
                "state": "paulus",
            },
            "variables": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"]["result"] is True

    await websocket_client.send_json_auto_id(
        {
            "type": "test_condition",
            "condition": {
                "condition": "template",
                "value_template": "{{ is_state('hello.world', 'paulus') }}",
            },
            "variables": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"]["result"] is True

    await websocket_client.send_json_auto_id(
        {
            "type": "test_condition",
            "condition": {
                "condition": "template",
                "value_template": "{{ is_state('hello.world', 'frenck') }}",
            },
            "variables": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"]["result"] is False