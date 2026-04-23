async def test_form_mfa(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_config_api: AsyncMock
) -> None:
    """Test MFA enabled on account configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    # Change the login mock to raise an MFA required error
    mock_config_api.return_value.login.side_effect = RequireMFAException("mfa_required")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "mfa_required"}
    assert result["step_id"] == "user"

    # Add a bad MFA Code response
    mock_config_api.return_value.multi_factor_authenticate.side_effect = KeyError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_MFA_CODE: "123456",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "bad_mfa"}
    assert result["step_id"] == "user"

    # Use a good MFA Code - Clear mock
    mock_config_api.return_value.multi_factor_authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_MFA_CODE: "123456",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Monarch Money"
    assert result["data"] == {
        CONF_TOKEN: "mocked_token",
    }
    assert result["result"].unique_id == "222260252323873333"

    assert len(mock_setup_entry.mock_calls) == 1