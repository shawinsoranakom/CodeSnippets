async def test_to_config_with_configured_builtin_tools() -> None:
    """Test _to_config with configured builtin tools."""
    client = AsyncOpenAI()
    tools = [
        {"type": "file_search", "vector_store_ids": ["vs1", "vs2"], "max_num_results": 10},  # type: ignore
        {"type": "web_search_preview", "user_location": "US", "search_context_size": 5},  # type: ignore
        {"type": "image_generation", "background": "white"},  # type: ignore
    ]
    agent = OpenAIAgent(
        name="configured_test",
        description="Test agent with configured tools",
        client=client,
        model="gpt-4o",
        instructions="Test instructions",
        tools=tools,  # type: ignore
    )

    config = agent.to_config()
    assert config.name == "configured_test"
    assert config.tools is not None
    assert len(config.tools) == 3

    # Verify configured tools are serialized correctly
    tool_configs = [tool for tool in config.tools if isinstance(tool, dict)]
    assert len(tool_configs) == 3

    # Check file_search config
    file_search_config = next(tool for tool in tool_configs if tool["type"] == "file_search")
    assert file_search_config["vector_store_ids"] == ["vs1", "vs2"]
    assert file_search_config["max_num_results"] == 10

    # Check web_search_preview config
    web_search_config = next(tool for tool in tool_configs if tool["type"] == "web_search_preview")
    assert web_search_config["user_location"] == "US"
    assert web_search_config["search_context_size"] == 5

    # Check image_generation config
    image_gen_config = next(tool for tool in tool_configs if tool["type"] == "image_generation")
    assert image_gen_config["background"] == "white"