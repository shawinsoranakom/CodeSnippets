async def test_notify_multiple_targets_if_any_disconnected(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    aioclient_mock: AiohttpClientMocker,
    setup_push_receiver,
    setup_websocket_channel_only_push,
    target: list[str] | None,
) -> None:
    """Notify works with disconnected targets.

    Test that although one target is disconnected,
    notify still works to other targets and the exception is still raised.
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

    # Setup the local push notification channel
    await client.send_json_auto_id(
        {
            "type": "mobile_app/push_notification_channel",
            "webhook_id": "mock-webhook_id",
        }
    )
    sub_result = await client.receive_json()
    assert sub_result["success"]
    sub_id = sub_result["id"]

    with pytest.raises(
        HomeAssistantError,
        match=r".*websocket-push-webhook-id.*not connected to local push notifications",
    ):
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

    # Assert that the notification has been sent to the local
    # push notification target that has been setup
    msg_result = await client.receive_json()
    assert msg_result["event"] == {"message": "Hello world"}
    assert msg_result["id"] == sub_id

    # Check that there are no more messages to receive (timeout expected)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(client.receive_json(), timeout=0.1)