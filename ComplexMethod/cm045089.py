async def test_config_serialization_with_complex_web_search() -> None:
    """Test config serialization with complex web_search_preview configuration."""
    client = AsyncOpenAI()
    tools = [
        {
            "type": "web_search_preview",
            "user_location": {"type": "approximate", "country": "US", "region": "CA", "city": "San Francisco"},
            "search_context_size": 10,
        }
    ]  # type: ignore
    agent = OpenAIAgent(
        name="complex_web_search_test",
        description="Test agent with complex web search config",
        client=client,
        model="gpt-4o",
        instructions="Test instructions",
        tools=tools,  # type: ignore
    )
    config = agent.to_config()
    assert config.tools is not None
    assert len(config.tools) == 1
    web_search_config = cast(Dict[str, Any], config.tools[0])
    assert isinstance(web_search_config, dict)
    assert web_search_config["type"] == "web_search_preview"
    user_location = web_search_config["user_location"]
    if isinstance(user_location, dict):
        assert user_location["type"] == "approximate"
        assert user_location["country"] == "US"
        assert user_location["region"] == "CA"
        assert user_location["city"] == "San Francisco"
    else:
        # If user_location is a string, just check value
        assert user_location == "US"
    assert web_search_config["search_context_size"] == 10
    # Test round-trip
    restored_agent = OpenAIAgent.from_config(config)
    restored_tool = cast(Dict[str, Any], restored_agent.tools[0])
    assert restored_tool["type"] == "web_search_preview"
    restored_user_location = restored_tool["user_location"]
    if isinstance(restored_user_location, dict):
        assert restored_user_location["type"] == "approximate"
        assert restored_user_location["country"] == "US"
        assert restored_user_location["region"] == "CA"
        assert restored_user_location["city"] == "San Francisco"
    else:
        assert restored_user_location == "US"
    assert restored_tool["search_context_size"] == 10