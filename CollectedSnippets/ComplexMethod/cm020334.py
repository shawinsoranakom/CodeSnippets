async def test_config_flow_pubsub_create_subscription_failure(
    hass: HomeAssistant,
    oauth: OAuthFixture,
    aioclient_mock: AiohttpClientMocker,
    auth: FakeAuth,
    mock_pubsub_api_responses: MockPubSubAPIResponses,
    create_subscription_status: HTTPStatus,
) -> None:
    """Check full flow fails with configuration error."""
    aioclient_mock.clear_requests()
    auth.register_mock_requests()
    mock_pubsub_api_responses.create_subscription_status = create_subscription_status
    mock_pubsub_api_responses.register_mock_requests()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await oauth.async_app_creds_flow(result)
    oauth.async_mock_refresh()

    result = await oauth.async_configure(result, {"code": "1234"})
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "pubsub_topic"
    assert result.get("data_schema")({}) == {
        "topic_name": f"projects/sdm-prod/topics/enterprise-{PROJECT_ID}",
    }

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
    assert result.get("data_schema")({}) == {
        "subscription_name": "create_new_subscription",
    }

    # Failure when creating the subscription
    result = await oauth.async_configure(
        result,
        {
            "subscription_name": "create_new_subscription",
        },
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"base": "pubsub_api_error"}

    # Reset the mock to allow success on the next attempt.
    aioclient_mock.clear_requests()
    auth.register_mock_requests()
    mock_pubsub_api_responses.create_subscription_status = HTTPStatus.OK
    mock_pubsub_api_responses.register_mock_requests()

    result = await oauth.async_configure(
        result,
        {
            "subscription_name": "create_new_subscription",
        },
    )
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