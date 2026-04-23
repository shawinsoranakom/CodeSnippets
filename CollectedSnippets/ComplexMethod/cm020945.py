async def test_config_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_touchlinesl_client: AsyncMock
) -> None:
    """Test the happy path where the provided username/password result in a new entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_DATA
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-username"
    assert result["data"] == CONFIG_DATA
    assert result["result"].unique_id == RESULT_UNIQUE_ID
    assert len(mock_setup_entry.mock_calls) == 1