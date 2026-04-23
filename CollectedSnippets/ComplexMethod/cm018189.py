async def test_call_service_child_not_found(
    hass: HomeAssistant, websocket_client
) -> None:
    """Test not reporting not found errors if it's not the called service."""

    async def serv_handler(call):
        await hass.services.async_call("non", "existing")

    hass.services.async_register("domain_test", "test_service", serv_handler)

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
    assert msg["error"]["code"] == const.ERR_HOME_ASSISTANT_ERROR
    assert (
        msg["error"]["message"] == "Service non.existing called service "
        "domain_test.test_service which was not found."
    )
    assert msg["error"]["translation_placeholders"] == {
        "domain": "domain_test",
        "service": "test_service",
        "child_domain": "non",
        "child_service": "existing",
    }
    assert msg["error"]["translation_key"] == "child_service_not_found"
    assert msg["error"]["translation_domain"] == "websocket_api"