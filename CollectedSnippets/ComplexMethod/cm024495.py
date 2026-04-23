async def test_form(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_mcp_client: Mock
) -> None:
    """Test the complete configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    response = Mock()
    response.serverInfo.name = TEST_API_NAME
    mock_mcp_client.return_value.initialize.return_value = response

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: MCP_SERVER_URL,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_API_NAME
    assert result["data"] == {
        CONF_URL: MCP_SERVER_URL,
    }
    # Config entry does not have a unique id
    assert result["result"]
    assert result["result"].unique_id is None

    assert len(mock_setup_entry.mock_calls) == 1