async def test_full_flow(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_waqi: AsyncMock
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "asd"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "World Air Quality Index"
    assert result["data"] == {CONF_API_KEY: "asd"}
    assert len(mock_setup_entry.mock_calls) == 1