async def __do_successful_otp_step(
    hass: HomeAssistant,
    result: ConfigFlowResult,
    mock_ituran: AsyncMock,
):
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_OTP: "123456",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Ituran {MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT]}"
    assert result["data"][CONF_ID_OR_PASSPORT] == MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT]
    assert result["data"][CONF_PHONE_NUMBER] == MOCK_CONFIG_DATA[CONF_PHONE_NUMBER]
    assert result["data"][CONF_MOBILE_ID] is not None
    assert result["result"].unique_id == MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT]
    assert len(mock_ituran.is_authenticated.mock_calls) > 0
    assert len(mock_ituran.authenticate.mock_calls) > 0

    return result