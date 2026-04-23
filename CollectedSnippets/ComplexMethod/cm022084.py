async def test_form_auth_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test that an auth flow without two factor succeeds."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "user"

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