async def test_reauth_exceptions(
    hass: HomeAssistant,
    mock_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    error: str,
) -> None:
    """Test reauth flow with exception during login and recovery."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_client.login.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    # Retry to show recovery.
    updated_auth = dataclasses.replace(
        AUTHENTICATION,
        access_token="new_access_token",
        refresh_token="new_refresh_token",
    )
    mock_client.login.return_value = updated_auth
    mock_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data == {
        CONF_ACCESS_TOKEN: "new_access_token",
        CONF_ACCESS_TOKEN_EXPIRES: AUTHENTICATION.access_token_expires,
        CONF_REFRESH_TOKEN: "new_refresh_token",
        CONF_REFRESH_TOKEN_EXPIRES: AUTHENTICATION.refresh_token_expires,
        CONF_USER_ID: AUTHENTICATION.user_id,
        CONF_EMAIL: AUTHENTICATION.email,
    }
    assert len(hass.config_entries.async_entries()) == 1