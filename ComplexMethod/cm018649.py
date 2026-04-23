async def test_webhook_get(hass: HomeAssistant, mock_client) -> None:
    """Test sending a get request to a webhook."""
    hooks = []
    webhook_id = webhook.async_generate_id()

    async def handle(*args):
        """Handle webhook."""
        hooks.append(args)

    webhook.async_register(
        hass, "test", "Test hook", webhook_id, handle, allowed_methods=["GET"]
    )

    resp = await mock_client.get(f"/api/webhook/{webhook_id}")
    assert resp.status == HTTPStatus.OK
    assert len(hooks) == 1
    assert hooks[0][0] is hass
    assert hooks[0][1] == webhook_id
    assert hooks[0][2].method == "GET"

    # Test that status is HTTPStatus.METHOD_NOT_ALLOWED even when GET is not allowed.
    webhook.async_unregister(hass, webhook_id)
    webhook.async_register(
        hass, "test", "Test hook", webhook_id, handle, allowed_methods=["PUT"]
    )
    resp = await mock_client.get(f"/api/webhook/{webhook_id}")
    assert resp.status == HTTPStatus.METHOD_NOT_ALLOWED
    assert len(hooks) == 1