async def test_no_eligible_topics(
    hass: HomeAssistant,
    oauth: OAuthFixture,
) -> None:
    """Test the case where there are no eligible pub/sub topics and the topic is created."""
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

    result = await oauth.async_complete_pubsub_flow(
        result,
        selected_topic="create_new_topic",
        selected_subscription="create_new_subscription",
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