async def test_call_service_not_found(
    hass: HomeAssistant, websocket_client: MockHAClientWebSocket
) -> None:
    """Test call service command."""
    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_NOT_FOUND
    assert msg["error"]["message"] == "Service domain_test.test_service not found."
    assert msg["error"]["translation_placeholders"] == {
        "domain": "domain_test",
        "service": "test_service",
    }
    assert msg["error"]["translation_key"] == "service_not_found"
    assert msg["error"]["translation_domain"] == "homeassistant"