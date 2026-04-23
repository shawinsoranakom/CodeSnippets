async def test_reauth_multiple_config_entries(
    hass: HomeAssistant, oauth, setup_platform, config_entry
) -> None:
    """Test Nest reauthentication with multiple existing config entries."""
    await setup_platform()

    old_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            **config_entry.data,
            "extra_data": True,
        },
    )
    old_entry.add_to_hass(hass)

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 2

    orig_subscriber_id = config_entry.data.get("subscriber_id")

    # Invoke the reauth flow
    result = await oauth.async_reauth(config_entry)

    await oauth.async_oauth_web_flow(result)
    oauth.async_mock_refresh()

    result = await oauth.async_finish_setup(result)
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reauth_successful"

    # Only reauth entry was updated, the other entry is preserved
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 2
    entry = entries[0]
    assert entry.unique_id == PROJECT_ID
    entry.data["token"].pop("expires_at")
    assert entry.data["token"] == {
        "refresh_token": "mock-refresh-token",
        "access_token": "mock-access-token",
        "type": "Bearer",
        "expires_in": 60,
    }
    assert entry.data.get("subscriber_id") == orig_subscriber_id  # Not updated
    assert not entry.data.get("extra_data")

    # Other entry was not refreshed
    entry = entries[1]
    entry.data["token"].pop("expires_at")
    assert entry.data.get("token", {}).get("access_token") == "some-token"
    assert entry.data.get("extra_data")