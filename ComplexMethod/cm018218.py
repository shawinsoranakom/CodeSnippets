async def test_cleanup_on_cancellation(
    hass: HomeAssistant, websocket_client: MockHAClientWebSocket
) -> None:
    """Test cleanup on cancellation."""

    subscriptions = None

    # Register a handler that registers a subscription
    @callback
    @websocket_command(
        {
            "type": "fake_subscription",
        }
    )
    def fake_subscription(
        hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
    ) -> None:
        nonlocal subscriptions
        msg_id: int = msg["id"]
        connection.subscriptions[msg_id] = callback(lambda: None)
        connection.send_result(msg_id)
        subscriptions = connection.subscriptions

    async_register_command(hass, fake_subscription)

    # Register a handler that raises on cancel
    @callback
    @websocket_command(
        {
            "type": "subscription_that_raises_on_cancel",
        }
    )
    def subscription_that_raises_on_cancel(
        hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
    ) -> None:
        nonlocal subscriptions
        msg_id: int = msg["id"]

        @callback
        def _raise():
            raise ValueError

        connection.subscriptions[msg_id] = _raise
        connection.send_result(msg_id)
        subscriptions = connection.subscriptions

    async_register_command(hass, subscription_that_raises_on_cancel)

    # Register a handler that cancels in handler
    @callback
    @websocket_command(
        {
            "type": "cancel_in_handler",
        }
    )
    def cancel_in_handler(
        hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
    ) -> None:
        raise asyncio.CancelledError

    async_register_command(hass, cancel_in_handler)

    await websocket_client.send_json({"id": 1, "type": "ping"})
    msg = await websocket_client.receive_json()
    assert msg["id"] == 1
    assert msg["type"] == "pong"
    assert not subscriptions
    await websocket_client.send_json({"id": 2, "type": "fake_subscription"})
    msg = await websocket_client.receive_json()
    assert msg["id"] == 2
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert len(subscriptions) == 2
    await websocket_client.send_json(
        {"id": 3, "type": "subscription_that_raises_on_cancel"}
    )
    msg = await websocket_client.receive_json()
    assert msg["id"] == 3
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert len(subscriptions) == 3
    await websocket_client.send_json({"id": 4, "type": "cancel_in_handler"})
    await hass.async_block_till_done()
    msg = await websocket_client.receive()
    assert msg.type == WSMsgType.close
    assert len(subscriptions) == 0