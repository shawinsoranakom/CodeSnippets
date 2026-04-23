async def test_config_serialization_with_mixed_tools() -> None:
    """Test config serialization with mixed string and configured tools."""
    client = AsyncOpenAI()
    tools = [
        "web_search_preview",  # string tool
        {"type": "file_search", "vector_store_ids": ["vs1"]},  # type: ignore
        "image_generation",  # string tool
        {"type": "code_interpreter", "container": "python-3.11"},  # type: ignore
    ]

    agent = OpenAIAgent(
        name="mixed_tools_test",
        description="Test agent with mixed tool types",
        client=client,
        model="gpt-4o",
        instructions="Test instructions",
        tools=tools,  # type: ignore
    )

    config = agent.to_config()
    assert config.tools is not None
    assert len(config.tools) == 4

    # Verify all tools are serialized as dicts with "type" key
    dict_tools = [tool for tool in config.tools if isinstance(tool, dict)]
    assert len(dict_tools) == 4

    # Check that string tools are converted to dicts with "type" key
    tool_types = [tool["type"] for tool in dict_tools]
    assert "web_search_preview" in tool_types
    assert "file_search" in tool_types
    assert "image_generation" in tool_types
    assert "code_interpreter" in tool_types

    # Verify configured tools preserve their configuration
    file_search_config = next(tool for tool in dict_tools if tool["type"] == "file_search")
    assert file_search_config["vector_store_ids"] == ["vs1"]

    code_interpreter_config = next(tool for tool in dict_tools if tool["type"] == "code_interpreter")
    assert code_interpreter_config["container"] == "python-3.11"