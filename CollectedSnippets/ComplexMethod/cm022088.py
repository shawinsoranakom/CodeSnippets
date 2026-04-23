async def test_form_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    auth_client: MagicMock,
    error_type: Exception,
    error_string: str,
) -> None:
    """Test we handle errors in the user step of the setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

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
    assert result["step_id"] == "user"

    # Make sure the config flow tests finish with either an
    # FlowResultType.CREATE_ENTRY or FlowResultType.ABORT so
    # we can show the config flow is able to recover from an error.
    auth_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: MOCKED_EMAIL,
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCKED_EMAIL
    assert result["data"] == {
        CONF_USER_ID: MOCKED_USER.user_id,
        CONF_AUTHORIZE_STRING: "test_authorize_string",
        CONF_EXPIRES_AT: ANY,
        CONF_ACCESS_TOKEN: "test_token",
        CONF_REFRESH_TOKEN: "test_refresh_token",
    }
    assert result["result"].unique_id == str(MOCKED_USER.user_id)
    assert len(mock_setup_entry.mock_calls) == 1