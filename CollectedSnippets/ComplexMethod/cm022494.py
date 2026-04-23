async def test_config_local_sdk_if_disabled(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test the local SDK."""
    assert await async_setup_component(hass, "webhook", {})

    config = MockConfig(
        hass=hass,
        agent_user_ids={
            "mock-user-id": {
                STORE_GOOGLE_LOCAL_WEBHOOK_ID: "mock-webhook-id",
            },
        },
        enabled=False,
    )
    assert not config.is_local_sdk_active

    client = await hass_client()

    config.async_enable_local_sdk()
    assert config.is_local_sdk_active

    resp = await client.post(
        "/api/webhook/mock-webhook-id", json={"requestId": "mock-req-id"}
    )
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {
        "payload": {"errorCode": "deviceTurnedOff"},
        "requestId": "mock-req-id",
    }

    config.async_disable_local_sdk()
    assert not config.is_local_sdk_active

    # Webhook is no longer active
    resp = await client.post("/api/webhook/mock-webhook-id")
    assert resp.status == HTTPStatus.OK
    assert await resp.read() == b""