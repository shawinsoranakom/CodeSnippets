async def test_call_service_target(
    hass: HomeAssistant, websocket_client: MockHAClientWebSocket
) -> None:
    """Test call service command with target."""
    calls = async_mock_service(hass, "domain_test", "test_service")

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
            "target": {
                "entity_id": ["entity.one", "entity.two"],
                "device_id": "deviceid",
            },
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    assert len(calls) == 1
    call = calls[0]

    assert call.domain == "domain_test"
    assert call.service == "test_service"
    assert call.data == {
        "hello": "world",
        "entity_id": ["entity.one", "entity.two"],
        "device_id": ["deviceid"],
    }
    assert call.context.as_dict() == msg["result"]["context"]