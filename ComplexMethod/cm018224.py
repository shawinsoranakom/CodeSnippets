async def test_enable_disable_debug_logging(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test enabling and disabling debug logging."""
    assert await async_setup_component(hass, "logger", {"logger": {}})
    async with async_call_logger_set_level(
        "homeassistant.components.websocket_api", "DEBUG", hass=hass, caplog=caplog
    ):
        await websocket_client.send_json({"id": 1, "type": "ping"})
        msg = await websocket_client.receive_json()
        assert msg["id"] == 1
        assert msg["type"] == "pong"
        assert 'Sending b\'{"id":1,"type":"pong"}\'' in caplog.text
    async with async_call_logger_set_level(
        "homeassistant.components.websocket_api", "WARNING", hass=hass, caplog=caplog
    ):
        await websocket_client.send_json({"id": 2, "type": "ping"})
        msg = await websocket_client.receive_json()
        assert msg["id"] == 2
        assert msg["type"] == "pong"
        assert 'Sending b\'{"id":2,"type":"pong"}\'' not in caplog.text