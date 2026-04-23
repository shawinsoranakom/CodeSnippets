async def test_full_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test the full config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "user_aaaaaaaaaa"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test"
    assert result["data"] == {CONF_API_KEY: "user_aaaaaaaaaa"}
    assert result["result"].unique_id == "30561"
    assert len(mock_setup_entry.mock_calls) == 1