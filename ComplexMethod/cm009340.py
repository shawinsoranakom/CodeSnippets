def test_reasoning_output_stream() -> None:
    """Test reasoning output from ChatGroq with stream."""
    chat = ChatGroq(
        model=REASONING_MODEL_NAME,
        reasoning_format="parsed",
    )
    message = [
        SystemMessage(
            content="You are a helpful assistant that translates English to French."
        ),
        HumanMessage(content="I love programming."),
    ]

    full_response: AIMessageChunk | None = None
    for token in chat.stream(message):
        assert isinstance(token, AIMessageChunk)

        if full_response is None:
            full_response = token
        else:
            # Casting since adding results in a type error
            full_response = cast("AIMessageChunk", full_response + token)

    assert full_response is not None
    assert isinstance(full_response, AIMessageChunk)
    assert "reasoning_content" in full_response.additional_kwargs
    assert isinstance(full_response.additional_kwargs["reasoning_content"], str)
    assert len(full_response.additional_kwargs["reasoning_content"]) > 0