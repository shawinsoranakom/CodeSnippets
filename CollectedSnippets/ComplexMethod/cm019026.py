async def test_webhook_msg(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test webhook msg."""
    with patch("hass_nabucasa.Cloud.initialize"):
        setup = await async_setup_component(hass, "cloud", {"cloud": {}})
        assert setup
    cloud = hass.data[DATA_CLOUD]

    await cloud.client.prefs.async_initialize()
    await cloud.client.prefs.async_update(
        cloudhooks={
            "mock-webhook-id": {
                "webhook_id": "mock-webhook-id",
                "cloudhook_id": "mock-cloud-id",
            },
            "no-longere-existing": {
                "webhook_id": "no-longere-existing",
                "cloudhook_id": "mock-nonexisting-id",
            },
        }
    )

    received = []

    async def handler(
        hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        """Handle a webhook."""
        received.append(request)
        return web.json_response({"from": "handler"})

    webhook.async_register(hass, "test", "Test", "mock-webhook-id", handler)

    response = await cloud.client.async_webhook_message(
        {
            "cloudhook_id": "mock-cloud-id",
            "body": '{"hello": "world"}',
            "headers": {"content-type": CONTENT_TYPE_JSON},
            "method": "POST",
            "query": None,
        }
    )

    assert response == {
        "status": 200,
        "body": '{"from": "handler"}',
        "headers": {"Content-Type": CONTENT_TYPE_JSON},
    }

    assert len(received) == 1
    assert await received[0].json() == {"hello": "world"}

    # Non existing webhook
    caplog.clear()

    response = await cloud.client.async_webhook_message(
        {
            "cloudhook_id": "mock-nonexisting-id",
            "body": '{"nonexisting": "payload"}',
            "headers": {"content-type": CONTENT_TYPE_JSON},
            "method": "POST",
            "query": None,
        }
    )

    assert response == {
        "status": 200,
        "body": None,
        "headers": {"Content-Type": "application/octet-stream"},
    }

    assert (
        "Received message for unregistered webhook no-longere-existing from cloud"
        in caplog.text
    )
    assert '{"nonexisting": "payload"}' in caplog.text