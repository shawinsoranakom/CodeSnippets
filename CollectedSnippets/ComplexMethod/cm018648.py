async def test_webhook_head(hass: HomeAssistant, mock_client) -> None:
    """Test sending a head request to a webhook."""
    hooks = []
    webhook_id = webhook.async_generate_id()

    async def handle(*args):
        """Handle webhook."""
        hooks.append(args)

    webhook.async_register(
        hass, "test", "Test hook", webhook_id, handle, allowed_methods=["HEAD"]
    )

    resp = await mock_client.head(f"/api/webhook/{webhook_id}")
    assert resp.status == HTTPStatus.OK
    assert len(hooks) == 1
    assert hooks[0][0] is hass
    assert hooks[0][1] == webhook_id
    assert hooks[0][2].method == "HEAD"

    # Test that status is HTTPStatus.OK even when HEAD is not allowed.
    webhook.async_unregister(hass, webhook_id)
    webhook.async_register(
        hass, "test", "Test hook", webhook_id, handle, allowed_methods=["PUT"]
    )
    resp = await mock_client.head(f"/api/webhook/{webhook_id}")
    assert resp.status == HTTPStatus.OK
    assert len(hooks) == 1