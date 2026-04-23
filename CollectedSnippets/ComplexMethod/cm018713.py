async def test_full_flow(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_server: AsyncMock
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_CONNECTION,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Snapcast"
    assert result["data"] == {CONF_HOST: "127.0.0.1", CONF_PORT: 1705}
    assert len(mock_setup_entry.mock_calls) == 1