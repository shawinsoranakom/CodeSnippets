async def test_ws_webhook(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test sending webhook msg via WS API."""
    assert await async_setup_component(hass, "webhook", {})

    received = []

    async def handler(
        hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        """Handle a webhook."""
        received.append(request)
        return web.json_response({"from": "handler"})

    webhook.async_register(hass, "test", "Test", "mock-webhook-id", handler)

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 5,
            "type": "webhook/handle",
            "webhook_id": "mock-webhook-id",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": '{"hello": "world"}',
            "query": "a=2",
        }
    )

    result = await client.receive_json()
    assert result["success"], result
    assert result["result"] == {
        "status": 200,
        "body": '{"from": "handler"}',
        "headers": {"Content-Type": "application/json"},
    }

    assert len(received) == 1
    assert received[0].headers["content-type"] == "application/json"
    assert received[0].query == {"a": "2"}
    assert await received[0].json() == {"hello": "world"}

    # Non existing webhook
    caplog.clear()

    await client.send_json(
        {
            "id": 6,
            "type": "webhook/handle",
            "webhook_id": "mock-nonexisting-id",
            "method": "POST",
            "body": '{"nonexisting": "payload"}',
        }
    )

    result = await client.receive_json()
    assert result["success"], result
    assert result["result"] == {
        "status": 200,
        "body": None,
        "headers": {"Content-Type": "application/octet-stream"},
    }

    assert (
        "Received message for unregistered webhook mock-nonexisting-id from webhook/ws"
        in caplog.text
    )
    assert '{"nonexisting": "payload"}' in caplog.text