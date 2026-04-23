async def test_dhcp_discovery_with_creds(
    hass: HomeAssistant,
    oauth: OAuthFixture,
    topic_args: dict[str, str],
    expected_config_entry_data: dict[str, Any],
) -> None:
    """Exercise discovery dhcp with no config present (can't run)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=FAKE_DHCP_DATA,
    )
    await hass.async_block_till_done()
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "oauth_discovery"

    result = await oauth.async_configure(result, {})
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "cloud_project"

    result = await oauth.async_configure(result, {"cloud_project_id": CLOUD_PROJECT_ID})
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "device_project"

    result = await oauth.async_configure(result, {"project_id": PROJECT_ID})
    await oauth.async_oauth_web_flow(result)
    oauth.async_mock_refresh()

    result = await oauth.async_configure(result, None)
    result = await oauth.async_complete_pubsub_flow(result, **topic_args)
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
        **expected_config_entry_data,
        "token": {
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
        },
    }