async def test_create_topic_failed(
    hass: HomeAssistant,
    oauth: OAuthFixture,
    aioclient_mock: AiohttpClientMocker,
    cloud_project_id: str,
    subscriptions: list[tuple[str, str]],
    auth: FakeAuth,
    mock_pubsub_api_responses: MockPubSubAPIResponses,
) -> None:
    """Test the case where there are no eligible pub/sub topics and the topic is created."""
    aioclient_mock.clear_requests()
    auth.register_mock_requests()
    mock_pubsub_api_responses.create_topic_status = HTTPStatus.INTERNAL_SERVER_ERROR
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
    # Option shown to create a new topic
    assert result.get("data_schema")({}) == {
        "topic_name": "create_new_topic",
    }

    result = await oauth.async_configure(result, {"topic_name": "create_new_topic"})
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "pubsub_topic"
    assert result.get("errors") == {"base": "pubsub_api_error"}

    # Re-register mock requests needed for the rest of the test. The topic
    # request will now succeed.
    aioclient_mock.clear_requests()
    setup_mock_create_topic_responses(aioclient_mock, cloud_project_id)
    # Fix up other mock responses cleared above
    auth.register_mock_requests()
    setup_mock_list_subscriptions_responses(
        aioclient_mock,
        cloud_project_id,
        subscriptions,
    )
    setup_mock_create_subscription_responses(aioclient_mock, cloud_project_id)

    result = await oauth.async_configure(result, {"topic_name": "create_new_topic"})
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "pubsub_topic_confirm"
    assert not result.get("errors")

    result = await oauth.async_configure(result, {})
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "pubsub_subscription"
    assert not result.get("errors")

    # Create a subscription for the topic and end the flow
    result = await oauth.async_finish_setup(
        result,
        {"subscription_name": "create_new_subscription"},
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
        "topic_name": f"projects/{CLOUD_PROJECT_ID}/topics/home-assistant-{RAND_SUFFIX}",
        "token": {
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
        },
    }