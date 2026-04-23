async def test_notify_works(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, setup_push_receiver
) -> None:
    """Test notify works."""
    assert hass.services.has_service("notify", "mobile_app_test") is True
    await hass.services.async_call(
        "notify",
        "mobile_app_test",
        {
            "message": "Hello world",
            "title": "Demo",
            "target": ["mock-webhook_id"],
            "data": {"field1": "value1"},
        },
        blocking=True,
    )

    assert len(aioclient_mock.mock_calls) == 1
    call = aioclient_mock.mock_calls

    call_json = call[0][2]

    assert call_json["push_token"] == "PUSH_TOKEN"
    assert call_json["message"] == "Hello world"
    assert call_json["title"] == "Demo"
    assert call_json["data"] == {"field1": "value1"}
    assert call_json["registration_info"]["app_id"] == "io.homeassistant.mobile_app"
    assert call_json["registration_info"]["app_version"] == "1.0"
    assert call_json["registration_info"]["webhook_id"] == "mock-webhook_id"