async def test_component_serialization(agent: OpenAIAgent) -> None:
    config = agent.dump_component()
    config_dict = config.config

    assert config_dict["name"] == "assistant"
    assert config_dict["description"] == "Test assistant using the Response API"
    assert config_dict["model"] == "gpt-4o"
    assert config_dict["instructions"] == "You are a helpful AI assistant."
    assert config_dict["temperature"] == 0.7
    assert config_dict["max_output_tokens"] == 1000
    assert config_dict["store"] is True
    assert config_dict["truncation"] == "auto"