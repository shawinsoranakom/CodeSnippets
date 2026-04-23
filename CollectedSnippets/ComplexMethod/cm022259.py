async def test_reauth_reconfigure_flow_invalid_phone_number(
    hass: HomeAssistant,
    mock_auth_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    flow_starter: Callable,
    expected_step_id: str,
    expected_sms_step_id: str,
    expected_reason: str,
) -> None:
    """Test reauth and reconfigure flows with invalid phone number."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await flow_starter(mock_config_entry, hass)

    mock_auth_client.request_sms_code.side_effect = (
        FressnapfTrackerInvalidPhoneNumberError
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: "invalid"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == expected_step_id
    assert result["errors"] == {"base": "invalid_phone_number"}

    # Recover from error
    mock_auth_client.request_sms_code.side_effect = None
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