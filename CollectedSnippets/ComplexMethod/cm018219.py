async def test_delayed_response_handler(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a handler that responds after a connection has already been closed."""

    subscriptions = None

    # Register a handler that responds after it returns
    @callback
    @websocket_command(
        {
            "type": "late_responder",
        }
    )
    def async_late_responder(
        hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
    ) -> None:
        msg_id: int = msg["id"]
        nonlocal subscriptions
        subscriptions = connection.subscriptions
        connection.subscriptions[msg_id] = lambda: None
        connection.send_result(msg_id)

        async def _async_late_send_message():
            await asyncio.sleep(0.05)
            connection.send_event(msg_id, {"event": "any"})

        hass.async_create_task(_async_late_send_message())

    async_register_command(hass, async_late_responder)

    await websocket_client.send_json({"id": 1, "type": "ping"})
    msg = await websocket_client.receive_json()
    assert msg["id"] == 1
    assert msg["type"] == "pong"
    assert not subscriptions
    await websocket_client.send_json({"id": 2, "type": "late_responder"})
    msg = await websocket_client.receive_json()
    assert msg["id"] == 2
    assert msg["type"] == "result"
    assert len(subscriptions) == 2
    assert await websocket_client.close()
    await hass.async_block_till_done()
    assert len(subscriptions) == 0

    assert "Tried to send message" in caplog.text
    assert "on closed connection" in caplog.text