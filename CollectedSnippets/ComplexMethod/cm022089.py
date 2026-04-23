async def test_form_reauth_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    auth_client: MagicMock,
    error_type: Exception,
    error_string: str,
) -> None:
    """Test we handle errors in the reauth flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    auth_client.login.side_effect = error_type
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_string}
    assert result["step_id"] == "reauth_confirm"

    # Make sure the config flow tests finish with FlowResultType.ABORT so
    # we can show the config flow is able to recover from an error.
    auth_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data == {
        CONF_USER_ID: MOCKED_USER.user_id,
        CONF_AUTHORIZE_STRING: "test_authorize_string",
        CONF_EXPIRES_AT: ANY,
        CONF_ACCESS_TOKEN: "test_token",
        CONF_REFRESH_TOKEN: "test_refresh_token",
    }
    assert len(mock_setup_entry.mock_calls) == 1