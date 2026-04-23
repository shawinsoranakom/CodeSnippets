async def test_errors(
    hass: HomeAssistant,
    mock_ituran: AsyncMock,
    mock_setup_entry: AsyncMock,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test connection errors during configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_ituran.request_otp.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ID_OR_PASSPORT: MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT],
            CONF_PHONE_NUMBER: MOCK_CONFIG_DATA[CONF_PHONE_NUMBER],
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": expected_error}

    mock_ituran.request_otp.side_effect = None
    result = await __do_successful_user_step(hass, result, mock_ituran)

    mock_ituran.authenticate.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_OTP: "123456",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}

    mock_ituran.authenticate.side_effect = None
    await __do_successful_otp_step(hass, result, mock_ituran)