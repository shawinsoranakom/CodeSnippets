async def test_config_flow_restart(
    hass: HomeAssistant,
    oauth: OAuthFixture,
    topic_args: dict[str, str],
    expected_config_entry_data: dict[str, Any],
) -> None:
    """Check with auth implementation is re-initialized when aborting the flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await oauth.async_app_creds_flow(result)
    oauth.async_mock_refresh()

    # At this point, we should have a valid auth implementation configured.
    # Simulate aborting the flow and starting over to ensure we get prompted
    # again to configure everything.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "cloud_project"

    # Change the values to show they are reflected below
    result = await oauth.async_configure(
        result, {"cloud_project_id": "new-cloud-project-id"}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "device_project"

    result = await oauth.async_configure(result, {"project_id": "new-project-id"})
    await oauth.async_oauth_web_flow(result, "new-project-id")
    oauth.async_mock_refresh()

    result = await oauth.async_configure(result, {"code": "1234"})
    result = await oauth.async_complete_pubsub_flow(
        result,
        **topic_args,
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("context", {}).get("unique_id") == "new-project-id"

    entry = oauth.get_config_entry()
    data = dict(entry.data)
    assert "token" in data
    data["token"].pop("expires_in")
    data["token"].pop("expires_at")
    assert data == {
        "sdm": {},
        "auth_implementation": "imported-cred",
        "cloud_project_id": "new-cloud-project-id",
        "project_id": "new-project-id",
        **expected_config_entry_data,
        "token": {
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
        },
    }