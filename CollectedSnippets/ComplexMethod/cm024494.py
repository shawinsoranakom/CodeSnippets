async def test_call_tool(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_mcp_client: Mock
) -> None:
    """Test calling an MCP Tool through the LLM API."""
    mock_mcp_client.return_value.list_tools.return_value = ListToolsResult(
        tools=[SEARCH_MEMORY_TOOL]
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.LOADED

    apis = llm.async_get_apis(hass)
    api = next(iter([api for api in apis if api.name == TEST_API_NAME]))
    assert api

    api_instance = await api.async_get_api_instance(create_llm_context())
    assert len(api_instance.tools) == 1
    tool = api_instance.tools[0]
    assert tool.name == "search_memory"

    mock_mcp_client.return_value.call_tool.return_value = CallToolResult(
        content=[TextContent(type="text", text="User was born in February")]
    )
    result = await tool.async_call(
        hass,
        llm.ToolInput(
            tool_name="search_memory", tool_args={"query": "User's birth month"}
        ),
        create_llm_context(),
    )
    assert result == {
        "content": [{"text": "User was born in February", "type": "text"}]
    }