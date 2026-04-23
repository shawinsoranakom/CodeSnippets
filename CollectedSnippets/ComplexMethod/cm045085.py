async def test_from_config_with_configured_builtin_tools() -> None:
    """Test _from_config with configured builtin tools."""
    from autogen_ext.agents.openai._openai_agent import OpenAIAgentConfig  # type: ignore

    config = OpenAIAgentConfig(
        name="configured_from_config_test",
        description="Test agent with configured tools from config",
        model="gpt-4o",
        instructions="Test instructions",
        tools=[
            {"type": "file_search", "vector_store_ids": ["vs1"]},  # type: ignore
            {"type": "web_search_preview", "user_location": "US"},  # type: ignore
            {"type": "image_generation", "background": "black"},  # type: ignore
        ],
    )
    agent = OpenAIAgent.from_config(config)
    assert agent.name == "configured_from_config_test"
    assert agent.model == "gpt-4o"
    # Verify configured tools are loaded correctly
    assert len(agent.tools) == 3
    # Check file_search
    file_search_tool = next(tool for tool in agent.tools if tool["type"] == "file_search")
    assert file_search_tool["vector_store_ids"] == ["vs1"]
    # Check web_search_preview
    web_search_tool = next(tool for tool in agent.tools if tool["type"] == "web_search_preview")
    assert web_search_tool["user_location"] == "US"
    # Check image_generation
    image_gen_tool = next(tool for tool in agent.tools if tool["type"] == "image_generation")
    assert image_gen_tool["background"] == "black"