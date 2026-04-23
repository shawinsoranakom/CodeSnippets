async def _make_completion_request(
    client: openai.AsyncOpenAI,
    model_name: str,
) -> openai.types.Completion:
    """Make a single completion request and validate the response.

    Uses temperature=1.0 to ensure diverse outputs across concurrent
    requests for realistic load balancer testing.
    """
    completion = await client.completions.create(
        model=model_name,
        prompt="Hello, my name is",
        max_tokens=5,
        temperature=1.0,
    )

    assert completion.id is not None, (
        f"Expected non-None completion id. usage={completion.usage!r}"
    )
    assert completion.choices is not None and len(completion.choices) == 1, (
        f"Expected 1 choice, got "
        f"{len(completion.choices) if completion.choices else 'None'}"
    )

    choice = completion.choices[0]
    # With temperature=1.0, the model may emit a stop token immediately,
    # producing empty text with finish_reason='stop'. This is valid
    # model behavior - the test's purpose is load balancing, not output
    # quality.
    assert choice.finish_reason in ("length", "stop"), (
        f"Expected finish_reason 'length' or 'stop', "
        f"got {choice.finish_reason!r}. text={choice.text!r}"
    )
    if choice.finish_reason == "length":
        assert len(choice.text) >= 1, (
            f"Expected non-empty text with finish_reason='length', got {choice.text!r}"
        )

    assert completion.usage.prompt_tokens > 0, (
        f"Expected positive prompt_tokens, got {completion.usage.prompt_tokens}"
    )
    assert completion.usage.total_tokens > 0, (
        f"Expected positive total_tokens, got {completion.usage.total_tokens}"
    )
    return completion