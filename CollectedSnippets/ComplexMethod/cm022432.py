async def test_form_invalid_auth(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, suez_client: AsyncMock
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    suez_client.check_credentials.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_DATA,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    suez_client.check_credentials.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_DATA,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_DATA[CONF_COUNTER_ID]
    assert result["result"].unique_id == MOCK_DATA[CONF_COUNTER_ID]
    assert result["data"] == MOCK_DATA
    assert len(mock_setup_entry.mock_calls) == 1