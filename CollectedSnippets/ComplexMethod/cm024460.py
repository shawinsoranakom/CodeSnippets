async def test_notify_ws_confirming_works(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    setup_push_receiver,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test notify confirming works."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "mobile_app/push_notification_channel",
            "webhook_id": "mock-webhook_id",
            "support_confirm": True,
        }
    )

    sub_result = await client.receive_json()
    assert sub_result["success"]
    sub_id = sub_result["id"]

    # Sent a message that will be delivered locally
    await hass.services.async_call(
        "notify", "mobile_app_test", {"message": "Hello world"}, blocking=True
    )

    msg_result = await client.receive_json()
    confirm_id = msg_result["event"].pop("hass_confirm_id")
    assert confirm_id is not None
    assert msg_result["event"] == {"message": "Hello world"}

    # Try to confirm with incorrect confirm ID
    await client.send_json_auto_id(
        {
            "type": "mobile_app/push_notification_confirm",
            "webhook_id": "mock-webhook_id",
            "confirm_id": "incorrect-confirm-id",
        }
    )

    result = await client.receive_json()
    assert not result["success"]
    assert result["error"] == {
        "code": "not_found",
        "message": "Push notification channel not found",
    }

    # Confirm with correct confirm ID
    await client.send_json_auto_id(
        {
            "type": "mobile_app/push_notification_confirm",
            "webhook_id": "mock-webhook_id",
            "confirm_id": confirm_id,
        }
    )

    result = await client.receive_json()
    assert result["success"]

    # Drop local push channel and try to confirm another message
    await client.send_json_auto_id(
        {
            "type": "unsubscribe_events",
            "subscription": sub_id,
        }
    )
    sub_result = await client.receive_json()
    assert sub_result["success"]

    await client.send_json_auto_id(
        {
            "type": "mobile_app/push_notification_confirm",
            "webhook_id": "mock-webhook_id",
            "confirm_id": confirm_id,
        }
    )

    result = await client.receive_json()
    assert not result["success"]
    assert result["error"] == {
        "code": "not_found",
        "message": "Push notification channel not found",
    }