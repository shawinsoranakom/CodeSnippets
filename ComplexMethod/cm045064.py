async def test_from_config(agent: OpenAIAgent) -> None:
    config = agent.dump_component()

    with patch("openai.AsyncOpenAI"):
        loaded_agent = OpenAIAgent.load_component(config)

        assert loaded_agent.name == "assistant"
        assert loaded_agent.description == "Test assistant using the Response API"
        assert loaded_agent._model == "gpt-4o"  # type: ignore
        assert loaded_agent._instructions == "You are a helpful AI assistant."  # type: ignore
        assert loaded_agent._temperature == 0.7  # type: ignore
        assert loaded_agent._max_output_tokens == 1000  # type: ignore
        assert loaded_agent._store is True  # type: ignore
        assert loaded_agent._truncation == "auto"