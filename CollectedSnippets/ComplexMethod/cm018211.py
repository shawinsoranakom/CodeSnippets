async def test_execute_script_err_localization(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    raise_exception: HomeAssistantError,
    err_code: str,
) -> None:
    """Test testing a condition."""
    async_mock_service(
        hass, "domain_test", "test_service", raise_exception=raise_exception
    )

    await websocket_client.send_json_auto_id(
        {
            "type": "execute_script",
            "sequence": [
                {
                    "service": "domain_test.test_service",
                    "data": {"hello": "world"},
                },
                {"stop": "done", "response_variable": "service_result"},
            ],
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"] is False
    assert msg["error"]["code"] == err_code
    assert msg["error"]["message"] == "Some error"
    assert msg["error"]["translation_key"] == "test_error"
    assert msg["error"]["translation_domain"] == "test"
    assert msg["error"]["translation_placeholders"] == {"option": "bla"}