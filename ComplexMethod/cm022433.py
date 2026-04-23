async def test_form_auto_counter(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, suez_client: AsyncMock
) -> None:
    """Test form set counter if not set by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    partial_form = MOCK_DATA.copy()
    partial_form.pop(CONF_COUNTER_ID)
    suez_client.find_counter.side_effect = PySuezError("test counter not found")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        partial_form,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "counter_not_found"}

    suez_client.find_counter.side_effect = None
    suez_client.find_counter.return_value = MOCK_DATA[CONF_COUNTER_ID]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        partial_form,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_DATA[CONF_COUNTER_ID]
    assert result["result"].unique_id == MOCK_DATA[CONF_COUNTER_ID]
    assert result["data"] == MOCK_DATA
    assert len(mock_setup_entry.mock_calls) == 1