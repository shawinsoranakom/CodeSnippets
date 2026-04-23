async def test_title_failure_fallback(
    hass: HomeAssistant, oauth, mock_subscriber
) -> None:
    """Test exception handling when determining the structure names."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await oauth.async_app_creds_flow(result)
    oauth.async_mock_refresh()

    mock_subscriber.async_get_device_manager.side_effect = AuthException()

    result = await oauth.async_configure(result, {"code": "1234"})
    result = await oauth.async_complete_pubsub_flow(
        result, selected_topic=f"projects/sdm-prod/topics/enterprise-{PROJECT_ID}"
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("context", {}).get("unique_id") == PROJECT_ID

    entry = oauth.get_config_entry()
    assert entry.title == "Import from configuration.yaml"
    assert "token" in entry.data
    assert entry.data.get("cloud_project_id") == CLOUD_PROJECT_ID
    assert (
        entry.data.get("subscription_name")
        == f"projects/{CLOUD_PROJECT_ID}/subscriptions/home-assistant-{RAND_SUFFIX}"
    )
    assert (
        entry.data.get("topic_name")
        == f"projects/sdm-prod/topics/enterprise-{PROJECT_ID}"
    )