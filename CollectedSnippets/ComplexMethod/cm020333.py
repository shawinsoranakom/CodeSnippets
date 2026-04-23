async def test_config_flow_wrong_project_id(
    hass: HomeAssistant,
    oauth: OAuthFixture,
) -> None:
    """Check the case where the wrong project ids are entered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "cloud_project"

    result = await oauth.async_configure(result, {"cloud_project_id": CLOUD_PROJECT_ID})
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "device_project"

    # Enter the cloud project id instead of device access project id (really we just check
    # they are the same value which is never correct)
    result = await oauth.async_configure(result, {"project_id": CLOUD_PROJECT_ID})
    assert result["type"] is FlowResultType.FORM
    assert "errors" in result
    assert "project_id" in result["errors"]
    assert result["errors"]["project_id"] == "wrong_project_id"

    # Fix with a correct value and complete the rest of the flow
    result = await oauth.async_configure(result, {"project_id": PROJECT_ID})
    await oauth.async_oauth_web_flow(result)
    await hass.async_block_till_done()
    oauth.async_mock_refresh()

    result = await oauth.async_configure(result, {"code": "1234"})
    result = await oauth.async_complete_pubsub_flow(
        result, selected_topic="projects/sdm-prod/topics/enterprise-some-project-id"
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
        "subscription_name": "projects/cloud-id-9876/subscriptions/home-assistant-ABCDEF",
        "topic_name": "projects/sdm-prod/topics/enterprise-some-project-id",
        "token": {
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
        },
    }