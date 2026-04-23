async def test_config_flow(
    hass: HomeAssistant,
    ws_client: ClientFixture,
    oauth_fixture: OAuthFixture,
) -> None:
    """Test config flow with application credential registered."""
    client = await ws_client()

    await client.cmd_result(
        "create",
        {
            CONF_DOMAIN: TEST_DOMAIN,
            CONF_CLIENT_ID: CLIENT_ID,
            CONF_CLIENT_SECRET: CLIENT_SECRET,
        },
    )
    result = await hass.config_entries.flow.async_init(
        TEST_DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.EXTERNAL_STEP
    result = await oauth_fixture.complete_external_step(result)
    assert (
        result["data"].get("auth_implementation") == "fake_integration_some_client_id"
    )

    # Verify it is not possible to delete an in-use config entry
    resp = await client.cmd("delete", {"application_credentials_id": ID})
    assert not resp.get("success")
    assert "error" in resp
    assert resp["error"].get("code") == "home_assistant_error"
    assert (
        resp["error"].get("message")
        == "Cannot delete credential in use by integration fake_integration"
    )

    # Return information about the in use config entry
    entries = hass.config_entries.async_entries(TEST_DOMAIN)
    assert len(entries) == 1
    client = await ws_client()
    result = await client.cmd_result(
        "config_entry", {"config_entry_id": entries[0].entry_id}
    )
    assert result.get("application_credentials_id") == ID

    # Delete the config entry
    await hass.config_entries.async_remove(entries[0].entry_id)

    # Application credential can now be removed
    resp = await client.cmd("delete", {"application_credentials_id": ID})
    assert resp.get("success")

    # Config entry information no longer found
    result = await client.cmd("config_entry", {"config_entry_id": entries[0].entry_id})
    assert "error" in result
    assert result["error"].get("code") == "invalid_config_entry_id"