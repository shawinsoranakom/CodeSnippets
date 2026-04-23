async def test_config_serialization_with_local_shell() -> None:
    """Test config serialization with local_shell tool (model-restricted)."""
    client = AsyncOpenAI()
    tools = ["local_shell"]  # type: ignore

    agent = OpenAIAgent(
        name="local_shell_test",
        description="Test agent with local_shell",
        client=client,
        model="codex-mini-latest",  # Required for local_shell
        instructions="Test instructions",
        tools=tools,  # type: ignore
    )

    config = agent.to_config()
    assert config.model == "codex-mini-latest"
    assert config.tools is not None
    assert len(config.tools) == 1
    # Built-in tools are serialized as dicts with "type" key
    assert config.tools[0] == {"type": "local_shell"}

    # Test round-trip
    restored_agent = OpenAIAgent.from_config(config)
    assert restored_agent.model == "codex-mini-latest"
    assert len(restored_agent.tools) == 1
    assert restored_agent.tools[0]["type"] == "local_shell"