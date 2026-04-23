async def test_correct_flow(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_arve: AsyncMock
) -> None:
    """Test the whole flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == USER_INPUT
    assert len(mock_setup_entry.mock_calls) == 1
    assert result2["result"].unique_id == "12345"