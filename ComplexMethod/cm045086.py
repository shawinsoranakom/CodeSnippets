async def test_round_trip_config_serialization() -> None:
    """Test round-trip serialization: agent -> config -> agent."""
    client = AsyncOpenAI()
    original_tools = [
        "web_search_preview",
        {"type": "file_search", "vector_store_ids": ["vs1"]},  # type: ignore
        {"type": "image_generation", "background": "white"},  # type: ignore
    ]

    original_agent = OpenAIAgent(
        name="round_trip_test",
        description="Test round-trip serialization",
        client=client,
        model="gpt-4o",
        instructions="Test instructions",
        tools=original_tools,  # type: ignore
    )

    # Serialize to config
    config = original_agent.to_config()

    # Deserialize back to agent
    restored_agent = OpenAIAgent.from_config(config)

    # Verify basic properties
    assert restored_agent.name == original_agent.name
    assert restored_agent.description == original_agent.description
    assert restored_agent.model == original_agent.model
    orig_config = original_agent.to_config()
    restored_config = restored_agent.to_config()
    assert restored_config.instructions == orig_config.instructions

    # Verify tools are preserved
    assert len(restored_agent.tools) == len(original_agent.tools)

    # Check that string tools are preserved
    assert any(tool["type"] == "web_search_preview" for tool in restored_agent.tools)

    # Check that configured tools are preserved
    file_search_tool = next(tool for tool in restored_agent.tools if tool["type"] == "file_search")
    assert file_search_tool["vector_store_ids"] == ["vs1"]

    image_gen_tool = next(tool for tool in restored_agent.tools if tool["type"] == "image_generation")
    assert image_gen_tool["background"] == "white"