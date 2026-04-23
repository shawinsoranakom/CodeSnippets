async def test_to_config_with_string_builtin_tools() -> None:
    """Test _to_config with string-based builtin tools."""
    client = AsyncOpenAI()
    tools = ["web_search_preview", "image_generation"]  # type: ignore
    agent = OpenAIAgent(
        name="config_test",
        description="Test agent for config serialization",
        client=client,
        model="gpt-4o",
        instructions="Test instructions",
        tools=tools,  # type: ignore
    )

    config = agent.to_config()
    assert config.name == "config_test"
    assert config.description == "Test agent for config serialization"
    assert config.model == "gpt-4o"
    assert config.instructions == "Test instructions"
    assert config.tools is not None
    assert len(config.tools) == 2

    # Verify tools are serialized correctly
    tool_types: list[str] = []
    for tool in config.tools:
        if isinstance(tool, str):
            tool_types.append(tool)
        elif isinstance(tool, dict):
            tool_types.append(tool["type"])
        else:
            # Handle ComponentModel case
            tool_types.append(str(tool))
    assert "web_search_preview" in tool_types
    assert "image_generation" in tool_types