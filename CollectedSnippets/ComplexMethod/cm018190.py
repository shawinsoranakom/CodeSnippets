async def test_call_service_schema_validation_error(
    hass: HomeAssistant, websocket_client
) -> None:
    """Test call service command with invalid service data."""

    calls = []
    service_schema = vol.Schema(
        {
            vol.Required("message"): str,
        }
    )

    @callback
    def service_call(call):
        calls.append(call)

    hass.services.async_register(
        "domain_test",
        "test_service",
        service_call,
        schema=service_schema,
    )

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {},
        }
    )
    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_INVALID_FORMAT

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"extra_key": "not allowed"},
        }
    )
    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_INVALID_FORMAT

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"message": []},
        }
    )
    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_INVALID_FORMAT

    assert len(calls) == 0