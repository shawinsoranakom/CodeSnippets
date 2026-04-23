async def test_notify_ws_works(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    setup_push_receiver,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test notify works."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "mobile_app/push_notification_channel",
            "webhook_id": "mock-webhook_id",
        }
    )

    sub_result = await client.receive_json()
    assert sub_result["success"]

    # Subscribe twice, it should forward all messages to 2nd subscription
    await client.send_json_auto_id(
        {
            "type": "mobile_app/push_notification_channel",
            "webhook_id": "mock-webhook_id",
        }
    )

    sub_result = await client.receive_json()
    assert sub_result["success"]
    new_sub_id = sub_result["id"]

    await hass.services.async_call(
        "notify", "mobile_app_test", {"message": "Hello world"}, blocking=True
    )

    assert len(aioclient_mock.mock_calls) == 0

    msg_result = await client.receive_json()
    assert msg_result["event"] == {"message": "Hello world"}
    assert msg_result["id"] == new_sub_id  # This is the new subscription

    # Unsubscribe, now it should go over http
    await client.send_json_auto_id(
        {
            "type": "unsubscribe_events",
            "subscription": new_sub_id,
        }
    )
    sub_result = await client.receive_json()
    assert sub_result["success"]

    await hass.services.async_call(
        "notify", "mobile_app_test", {"message": "Hello world 2"}, blocking=True
    )

    assert len(aioclient_mock.mock_calls) == 1

    # Test non-existing webhook ID
    await client.send_json_auto_id(
        {
            "type": "mobile_app/push_notification_channel",
            "webhook_id": "non-existing",
        }
    )
    sub_result = await client.receive_json()
    assert not sub_result["success"]
    assert sub_result["error"] == {
        "code": "not_found",
        "message": "Webhook ID not found",
    }

    # Test webhook ID linked to other user
    await client.send_json_auto_id(
        {
            "type": "mobile_app/push_notification_channel",
            "webhook_id": "webhook_id_2",
        }
    )
    sub_result = await client.receive_json()
    assert not sub_result["success"]
    assert sub_result["error"] == {
        "code": "unauthorized",
        "message": "User not linked to this webhook ID",
    }