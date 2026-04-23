async def test_from_config_with_string_builtin_tools() -> None:
    """Test _from_config with string-based builtin tools."""
    from autogen_ext.agents.openai._openai_agent import OpenAIAgentConfig  # type: ignore

    config = OpenAIAgentConfig(
        name="from_config_test",
        description="Test agent from config",
        model="gpt-4o",
        instructions="Test instructions",
        tools=["web_search_preview", "image_generation"],  # type: ignore
    )
    agent = OpenAIAgent.from_config(config)
    assert agent.name == "from_config_test"
    assert agent.description == "Test agent from config"
    assert agent.model == "gpt-4o"
    # Verify instructions via configuration
    assert agent.to_config().instructions == "Test instructions"
    # Verify tools are loaded correctly
    assert len(agent.tools) == 2
    tool_types = [tool["type"] for tool in agent.tools]
    assert "web_search_preview" in tool_types
    assert "image_generation" in tool_types