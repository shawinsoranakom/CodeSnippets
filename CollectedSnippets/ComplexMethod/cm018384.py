async def test_full_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@test.com",
            CONF_PASSWORD: "yes",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@test.com"
    assert result["data"] == {CONF_ACCESS_TOKEN: TOKEN}
    assert result["result"].unique_id == "a0226b8f-98fe-4524-b369-272b466b8797"
    assert len(mock_setup_entry.mock_calls) == 1