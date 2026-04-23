async def test_errors_and_recover(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_pyotp: MagicMock,
    exception: Exception,
    error: str,
) -> None:
    """Test errors and recover."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    mock_pyotp.TOTP().now.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_pyotp.TOTP().now.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OTP Sensor"
    assert result["data"] == TEST_DATA_RESULT
    assert len(mock_setup_entry.mock_calls) == 1