async def test_form(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, suez_client: AsyncMock
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

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