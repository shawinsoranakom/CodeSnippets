async def test_build_api_params(agent: OpenAIAgent) -> None:
    agent._last_response_id = None  # type: ignore
    params = agent._build_api_parameters([{"role": "user", "content": "hi"}])  # type: ignore
    assert "previous_response_id" not in params
    agent._last_response_id = "resp-456"  # type: ignore
    params = agent._build_api_parameters([{"role": "user", "content": "hi"}])  # type: ignore
    assert params.get("previous_response_id") == "resp-456"

    assert "max_tokens" not in params
    assert params.get("max_output_tokens") == 1000

    assert params.get("store") is True
    assert params.get("truncation") == "auto"

    agent._json_mode = True  # type: ignore
    params = agent._build_api_parameters([{"role": "user", "content": "hi"}])  # type: ignore
    assert "text.format" not in params
    assert params.get("text") == {"type": "json_object"}