async def test_form_invalid_auth(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_config_api: AsyncMock
) -> None:
    """Test config flow with a login error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    # Change the login mock to raise an MFA required error
    mock_config_api.return_value.login.side_effect = LoginFailedException(
        "Invalid Auth"
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    mock_config_api.return_value.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Monarch Money"
    assert result["data"] == {
        CONF_TOKEN: "mocked_token",
    }
    assert result["context"]["unique_id"] == "222260252323873333"
    assert len(mock_setup_entry.mock_calls) == 1