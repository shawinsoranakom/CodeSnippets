async def test_generate_new_token_errors(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_pyotp
) -> None:
    """Test input validation errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA_3,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_token"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA_2,
    )
    mock_pyotp.TOTP().verify.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: "123456"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_code"}

    mock_pyotp.TOTP().verify.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: "123456"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OTP Sensor"
    assert result["data"] == TEST_DATA_RESULT
    assert len(mock_setup_entry.mock_calls) == 1