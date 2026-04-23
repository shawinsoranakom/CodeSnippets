async def test_stream_no_reasoning(model: str, use_async: bool) -> None:
    """Test streaming with `reasoning=False`."""
    llm = ChatOllama(model=model, num_ctx=2**12, reasoning=False)
    messages = [
        {
            "role": "user",
            "content": SAMPLE,
        }
    ]
    result = None
    if use_async:
        async for chunk in llm.astream(messages):
            assert isinstance(chunk, BaseMessageChunk)
            if result is None:
                result = chunk
                continue
            result += chunk
    else:
        for chunk in llm.stream(messages):
            assert isinstance(chunk, BaseMessageChunk)
            if result is None:
                result = chunk
                continue
            result += chunk
    assert isinstance(result, AIMessageChunk)
    assert result.content
    assert "<think>" not in result.content
    assert "</think>" not in result.content
    assert "reasoning_content" not in result.additional_kwargs