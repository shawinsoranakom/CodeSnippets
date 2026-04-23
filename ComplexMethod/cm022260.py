async def test_reauth_reconfigure_flow_invalid_user_id(
    hass: HomeAssistant,
    mock_auth_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    flow_starter: Callable,
    expected_step_id: str,
    expected_sms_step_id: str,
    expected_reason: str,
) -> None:
    """Test reauth and reconfigure flows do not allow changing to another account."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await flow_starter(mock_config_entry, hass)

    mock_auth_client.request_sms_code = AsyncMock(
        return_value=SmsCodeResponse(id=MOCK_USER_ID + 1)
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: f"{MOCK_PHONE_NUMBER}123"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == expected_step_id
    assert result["errors"] == {"base": "account_change_not_allowed"}

    # Recover from error
    mock_auth_client.request_sms_code = AsyncMock(
        return_value=SmsCodeResponse(id=MOCK_USER_ID)
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == expected_sms_step_id

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "0123456"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == expected_reason