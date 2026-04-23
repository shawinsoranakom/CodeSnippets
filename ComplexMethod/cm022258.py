async def test_user_flow_request_sms_code_errors(
    hass: HomeAssistant,
    mock_auth_client: MagicMock,
    side_effect: Exception,
    error: str,
) -> None:
    """Test user flow with errors."""
    mock_auth_client.request_sms_code.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: "invalid"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error}

    # Recover from error
    mock_auth_client.request_sms_code.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "sms_code"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "0123456"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY