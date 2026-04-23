async def test_binary_message(
    hass: HomeAssistant, websocket_client, caplog: pytest.LogCaptureFixture
) -> None:
    """Test binary messages."""
    binary_payloads = {
        104: ([], asyncio.Future()),
        105: ([], asyncio.Future()),
    }

    # Register a handler
    @callback
    @websocket_command(
        {
            "type": "get_binary_message_handler",
        }
    )
    def get_binary_message_handler(
        hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
    ):
        unsub = None

        @callback
        def binary_message_handler(
            hass: HomeAssistant, connection: ActiveConnection, payload: bytes
        ):
            nonlocal unsub
            if msg["id"] == 103:
                raise ValueError("Boom")

            if payload:
                binary_payloads[msg["id"]][0].append(payload)
            else:
                binary_payloads[msg["id"]][1].set_result(
                    b"".join(binary_payloads[msg["id"]][0])
                )
                unsub()

        prefix, unsub = connection.async_register_binary_handler(binary_message_handler)

        connection.send_result(msg["id"], {"prefix": prefix})

    async_register_command(hass, get_binary_message_handler)

    # Register multiple binary handlers
    for i in range(101, 106):
        await websocket_client.send_json(
            {"id": i, "type": "get_binary_message_handler"}
        )
        result = await websocket_client.receive_json()
        assert result["id"] == i
        assert result["type"] == const.TYPE_RESULT
        assert result["success"]
        assert result["result"]["prefix"] == i - 100

    # Send message to binary
    await websocket_client.send_bytes((0).to_bytes(1, "big") + b"test0")
    await websocket_client.send_bytes((3).to_bytes(1, "big") + b"test3")
    await websocket_client.send_bytes((3).to_bytes(1, "big") + b"test3")
    await websocket_client.send_bytes((10).to_bytes(1, "big") + b"test10")
    await websocket_client.send_bytes((4).to_bytes(1, "big") + b"test4")
    await websocket_client.send_bytes((4).to_bytes(1, "big") + b"")
    await websocket_client.send_bytes((5).to_bytes(1, "big") + b"test5")
    await websocket_client.send_bytes((5).to_bytes(1, "big") + b"test5-2")
    await websocket_client.send_bytes((5).to_bytes(1, "big") + b"")

    # Verify received
    assert await binary_payloads[104][1] == b"test4"
    assert await binary_payloads[105][1] == b"test5test5-2"
    assert "Error handling binary message" in caplog.text
    assert "Received binary message for non-existing handler 0" in caplog.text
    assert "Received binary message for non-existing handler 3" in caplog.text
    assert "Received binary message for non-existing handler 10" in caplog.text