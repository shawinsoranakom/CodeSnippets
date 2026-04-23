def test_minimal_reasoning_effort_payload(
    use_max_completion_tokens: bool, use_responses_api: bool
) -> None:
    """Test that minimal reasoning effort is included in request payload."""
    if use_max_completion_tokens:
        kwargs = {"max_completion_tokens": 100}
    else:
        kwargs = {"max_tokens": 100}

    init_kwargs: dict[str, Any] = {
        "model": "gpt-5",
        "reasoning_effort": "minimal",
        "use_responses_api": use_responses_api,
        **kwargs,
    }

    llm = ChatOpenAI(**init_kwargs)

    messages = [
        {"role": "developer", "content": "respond with just 'test'"},
        {"role": "user", "content": "hello"},
    ]

    payload = llm._get_request_payload(messages, stop=None)

    # When using responses API, reasoning_effort becomes reasoning.effort
    if use_responses_api:
        assert "reasoning" in payload
        assert payload["reasoning"]["effort"] == "minimal"
        # For responses API, tokens param becomes max_output_tokens
        assert payload["max_output_tokens"] == 100
    else:
        # For non-responses API, reasoning_effort remains as is
        assert payload["reasoning_effort"] == "minimal"
        if use_max_completion_tokens:
            assert payload["max_completion_tokens"] == 100
        else:
            # max_tokens gets converted to max_completion_tokens in non-responses API
            assert payload["max_completion_tokens"] == 100