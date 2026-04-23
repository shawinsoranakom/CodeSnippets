async def test_pubsub_subscriber_config_entry_reauth(
    hass: HomeAssistant,
    oauth: OAuthFixture,
    setup_platform: PlatformSetup,
    config_entry: MockConfigEntry,
) -> None:
    """Test the pubsub subscriber id is preserved during reauth."""
    await setup_platform()

    result = await oauth.async_reauth(config_entry)
    await oauth.async_oauth_web_flow(result)
    oauth.async_mock_refresh()

    # Entering an updated access token refreshes the config entry.
    result = await oauth.async_finish_setup(result, {"code": "1234"})
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reauth_successful"

    entry = oauth.get_config_entry()
    entry.data["token"].pop("expires_at")
    assert entry.unique_id == PROJECT_ID
    assert entry.data["token"] == {
        "refresh_token": "mock-refresh-token",
        "access_token": "mock-access-token",
        "type": "Bearer",
        "expires_in": 60,
    }
    assert entry.data["auth_implementation"] == "imported-cred"
    assert entry.data["subscriber_id"] == SUBSCRIBER_ID
    assert entry.data["cloud_project_id"] == CLOUD_PROJECT_ID