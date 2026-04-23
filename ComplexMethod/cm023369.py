async def test_full_flow(
    hass: HomeAssistant, mock_nsapi: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test successful user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: API_KEY}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Nederlandse Spoorwegen"
    assert result["data"] == {CONF_API_KEY: API_KEY}
    assert len(mock_setup_entry.mock_calls) == 1