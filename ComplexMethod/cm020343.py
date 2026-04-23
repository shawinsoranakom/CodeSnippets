async def test_list_subscriptions_failure(
    hass: HomeAssistant,
    oauth: OAuthFixture,
    aioclient_mock: AiohttpClientMocker,
    auth: FakeAuth,
    mock_pubsub_api_responses: MockPubSubAPIResponses,
) -> None:
    """Test selecting existing user managed topic and subscription."""
    aioclient_mock.clear_requests()
    auth.register_mock_requests()
    mock_pubsub_api_responses.list_subscriptions_status = (
        HTTPStatus.INTERNAL_SERVER_ERROR
    )
    mock_pubsub_api_responses.register_mock_requests()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await oauth.async_app_creds_flow(result)
    oauth.async_mock_refresh()

    result = await oauth.async_configure(result, None)
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "pubsub_topic"
    assert not result.get("errors")

    # Select Pub/Sub topic the show available subscriptions (none)
    result = await oauth.async_configure(
        result,
        {
            "topic_name": f"projects/sdm-prod/topics/enterprise-{PROJECT_ID}",
        },
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "pubsub_topic_confirm"
    assert not result.get("errors")

    result = await oauth.async_configure(result, {})
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "pubsub_subscription"
    assert result.get("errors") == {"base": "pubsub_api_error"}

    # Continue with the rest of the flow but clear the mocks so that the
    # flow will now succeed.
    aioclient_mock.clear_requests()
    auth.register_mock_requests()
    mock_pubsub_api_responses.register_mock_requests()

    result = await oauth.async_configure(result, {})
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("context", {}).get("unique_id") == PROJECT_ID

    entry = oauth.get_config_entry()
    data = dict(entry.data)
    assert "token" in data
    data["token"].pop("expires_in")
    data["token"].pop("expires_at")
    assert data == {
        "sdm": {},
        "auth_implementation": "imported-cred",
        "cloud_project_id": CLOUD_PROJECT_ID,
        "project_id": PROJECT_ID,
        "subscription_name": f"projects/{CLOUD_PROJECT_ID}/subscriptions/home-assistant-{RAND_SUFFIX}",
        "topic_name": f"projects/sdm-prod/topics/enterprise-{PROJECT_ID}",
        "token": {
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
        },
    }