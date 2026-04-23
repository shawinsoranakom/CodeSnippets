async def test_notify_multiple_targets(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    aioclient_mock: AiohttpClientMocker,
    setup_push_receiver,
    setup_websocket_channel_only_push,
    target: list[str] | None,
) -> None:
    """Test notify to multiple targets.

    Messages will be sent to three targerts, one (with webhook id `webhook_id_2`) will be remote target
    and will send the notification via HTTP request, the other two (`mock-webhook_id` and`websocket-push-webhook-id`)
    will be local push only and will be sent via websocket.
    """

    # Setup mock for non-local push notification target
    # with webhook_id "webhook_id_2"
    aioclient_mock.post(
        "https://mobile-push.home-assistant.dev/push2",
        json={
            "rateLimits": {
                "attempts": 1,
                "successful": 1,
                "errors": 0,
                "total": 1,
                "maximum": 150,
                "remaining": 149,
                "resetsAt": (datetime.now() + timedelta(hours=24)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            }
        },
    )

    client = await hass_ws_client(hass)

    # Setup local push notification channels
    local_push_sub_ids = []
    for webhook_id in ("mock-webhook_id", "websocket-push-webhook-id"):
        await client.send_json_auto_id(
            {
                "type": "mobile_app/push_notification_channel",
                "webhook_id": webhook_id,
            }
        )
        sub_result = await client.receive_json()
        assert sub_result["success"]
        local_push_sub_ids.append(sub_result["id"])

    await hass.services.async_call(
        "notify",
        "notify",
        {
            "message": "Hello world",
            "target": target,
        },
        blocking=True,
    )

    # Assert that the notification has been sent to the non-local push notification target
    assert len(aioclient_mock.mock_calls) == 1
    call = aioclient_mock.mock_calls
    call_json = call[0][2]
    assert call_json["push_token"] == "PUSH_TOKEN2"
    assert call_json["message"] == "Hello world"
    assert call_json["registration_info"]["app_id"] == "io.homeassistant.mobile_app"
    assert call_json["registration_info"]["app_version"] == "1.0"
    assert call_json["registration_info"]["webhook_id"] == "webhook_id_2"

    # Assert that the notification has been sent to the two local push notification targets
    for sub_id in local_push_sub_ids:
        msg_result = await client.receive_json()
        assert msg_result["event"] == {"message": "Hello world"}
        msg_id = msg_result["id"]
        assert msg_id == sub_id