async def test_user(
    hass: HomeAssistant,
    mock_api: AsyncMock,
    mock_helper: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test user initialized flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONF_DATA,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"
    assert result["data"] == CONF_DATA
    assert result["result"].unique_id == CONF_DATA[CONF_EMAIL]
    assert len(mock_setup_entry.mock_calls) == 1