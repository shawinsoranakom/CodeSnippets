async def test_full_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "my_secret_token"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "DrNykterstein"
    assert result["data"] == {CONF_API_TOKEN: "my_secret_token"}
    assert result["result"].unique_id == "drnykterstien"
    assert len(mock_setup_entry.mock_calls) == 1