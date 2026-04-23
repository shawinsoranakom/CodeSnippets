async def test_user_flow_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # Submit phone number
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "sms_code"

    # Submit SMS code
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_SMS_CODE: "0123456"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_PHONE_NUMBER
    assert result["data"] == {
        CONF_PHONE_NUMBER: MOCK_PHONE_NUMBER,
        CONF_USER_ID: MOCK_USER_ID,
        CONF_ACCESS_TOKEN: MOCK_ACCESS_TOKEN,
    }
    assert result["context"]["unique_id"] == str(MOCK_USER_ID)
    assert len(mock_setup_entry.mock_calls) == 1