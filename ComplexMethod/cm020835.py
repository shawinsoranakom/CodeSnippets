async def test_generate_new_token(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test form generate new token."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA_2,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CODE: "123456"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OTP Sensor"
    assert result["data"] == TEST_DATA_RESULT
    assert len(mock_setup_entry.mock_calls) == 1