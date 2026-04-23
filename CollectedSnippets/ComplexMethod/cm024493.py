async def test_llm_get_api_tools(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_mcp_client: Mock
) -> None:
    """Test MCP tools are returned as LLM API tools."""
    mock_mcp_client.return_value.list_tools.return_value = ListToolsResult(
        tools=[SEARCH_MEMORY_TOOL, SAVE_MEMORY_TOOL],
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.LOADED

    apis = llm.async_get_apis(hass)
    api = next(iter([api for api in apis if api.name == TEST_API_NAME]))
    assert api

    api_instance = await api.async_get_api_instance(create_llm_context())
    assert len(api_instance.tools) == 2
    tool = api_instance.tools[0]
    assert tool.name == "search_memory"
    assert tool.description == "Search memory for relevant context based on a query."
    with pytest.raises(
        vol.Invalid, match=re.escape("required key not provided @ data['query']")
    ):
        tool.parameters({})
    assert tool.parameters({"query": "frogs"}) == {"query": "frogs"}

    tool = api_instance.tools[1]
    assert tool.name == "save_memory"
    assert tool.description == "Save a memory context."
    with pytest.raises(
        vol.Invalid, match=re.escape("required key not provided @ data['context']")
    ):
        tool.parameters({})
    assert tool.parameters({"context": {"fact": "User was born in February"}}) == {
        "context": {"fact": "User was born in February"}
    }