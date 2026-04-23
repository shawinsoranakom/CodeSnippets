async def test_already_authenticated(
    hass: HomeAssistant, mock_ituran: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test user already authenticated configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_ituran.is_authenticated.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ID_OR_PASSPORT: MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT],
            CONF_PHONE_NUMBER: MOCK_CONFIG_DATA[CONF_PHONE_NUMBER],
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Ituran {MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT]}"
    assert result["data"][CONF_ID_OR_PASSPORT] == MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT]
    assert result["data"][CONF_PHONE_NUMBER] == MOCK_CONFIG_DATA[CONF_PHONE_NUMBER]
    assert result["data"][CONF_MOBILE_ID] == MOCK_CONFIG_DATA[CONF_MOBILE_ID]
    assert result["result"].unique_id == MOCK_CONFIG_DATA[CONF_ID_OR_PASSPORT]