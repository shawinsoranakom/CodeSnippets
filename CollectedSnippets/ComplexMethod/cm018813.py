async def test_user_flow(
    hass: HomeAssistant, mock_hyponcloud: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test a successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"
    assert result["data"] == TEST_USER_INPUT
    assert result["result"].unique_id == "2123456789123456789"
    assert len(mock_setup_entry.mock_calls) == 1