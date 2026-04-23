async def test_call_service_error(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    websocket_client: MockHAClientWebSocket,
) -> None:
    """Test call service command with error."""
    caplog.set_level(logging.ERROR)

    @callback
    def ha_error_call(_):
        raise HomeAssistantError(
            "error_message",
            translation_domain="test",
            translation_key="custom_error",
            translation_placeholders={"option": "bla"},
        )

    hass.services.async_register("domain_test", "ha_error", ha_error_call)

    @callback
    def service_error_call(_):
        raise ServiceValidationError(
            "error_message",
            translation_domain="test",
            translation_key="custom_error",
            translation_placeholders={"option": "bla"},
        )

    hass.services.async_register("domain_test", "service_error", service_error_call)

    async def unknown_error_call(_):
        raise ValueError("value_error")

    hass.services.async_register("domain_test", "unknown_error", unknown_error_call)

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "ha_error",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"] is False
    assert msg["error"]["code"] == "home_assistant_error"
    assert msg["error"]["message"] == "error_message"
    assert msg["error"]["translation_placeholders"] == {"option": "bla"}
    assert msg["error"]["translation_key"] == "custom_error"
    assert msg["error"]["translation_domain"] == "test"
    assert "Traceback" not in caplog.text

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "service_error",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"] is False
    assert msg["error"]["code"] == "service_validation_error"
    assert msg["error"]["message"] == "Validation error: error_message"
    assert msg["error"]["translation_placeholders"] == {"option": "bla"}
    assert msg["error"]["translation_key"] == "custom_error"
    assert msg["error"]["translation_domain"] == "test"
    assert "Traceback" not in caplog.text

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "unknown_error",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"] is False
    assert msg["error"]["code"] == "unknown_error"
    assert msg["error"]["message"] == "value_error"
    assert "Traceback" in caplog.text