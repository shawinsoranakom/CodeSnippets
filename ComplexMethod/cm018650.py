async def test_webhook_local_only(hass: HomeAssistant, mock_client) -> None:
    """Test posting a webhook with local only."""
    hass.config.components.add("cloud")

    hooks = []
    webhook_id = webhook.async_generate_id()

    async def handle(*args):
        """Handle webhook."""
        hooks.append((args[0], args[1], await args[2].text()))

    webhook.async_register(
        hass, "test", "Test hook", webhook_id, handle, local_only=True
    )

    resp = await mock_client.post(f"/api/webhook/{webhook_id}", json={"data": True})
    assert resp.status == HTTPStatus.OK
    assert len(hooks) == 1
    assert hooks[0][0] is hass
    assert hooks[0][1] == webhook_id
    assert hooks[0][2] == '{"data": true}'

    # Request from remote IP
    with patch(
        "homeassistant.components.webhook.ip_address",
        return_value=ip_address("123.123.123.123"),
    ):
        resp = await mock_client.post(f"/api/webhook/{webhook_id}", json={"data": True})
    assert resp.status == HTTPStatus.OK
    # No hook received
    assert len(hooks) == 1

    # Request from Home Assistant Cloud remote UI
    with patch(
        "hass_nabucasa.remote.is_cloud_request", Mock(get=Mock(return_value=True))
    ):
        resp = await mock_client.post(f"/api/webhook/{webhook_id}", json={"data": True})

    # No hook received
    assert resp.status == HTTPStatus.OK
    assert len(hooks) == 1