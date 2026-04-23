async def test_reauth_different_user_id_new(
    hass: HomeAssistant,
    mock_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reauth flow with different, new user ID updating the existing entry."""
    mock_config_entry.add_to_hass(hass)
    config_entries = hass.config_entries.async_entries()
    assert len(config_entries) == 1
    assert config_entries[0].unique_id == AUTHENTICATION.user_id

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    updated_auth = dataclasses.replace(AUTHENTICATION, user_id="new_user_id")
    mock_client.login.return_value = updated_auth
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data == {
        CONF_ACCESS_TOKEN: AUTHENTICATION.access_token,
        CONF_ACCESS_TOKEN_EXPIRES: AUTHENTICATION.access_token_expires,
        CONF_REFRESH_TOKEN: AUTHENTICATION.refresh_token,
        CONF_REFRESH_TOKEN_EXPIRES: AUTHENTICATION.refresh_token_expires,
        CONF_USER_ID: "new_user_id",
        CONF_EMAIL: AUTHENTICATION.email,
    }
    config_entries = hass.config_entries.async_entries()
    assert len(config_entries) == 1
    assert config_entries[0].unique_id == "new_user_id"