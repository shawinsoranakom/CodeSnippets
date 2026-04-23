async def test_stream_reasoning_none(model: str, use_async: bool) -> None:
    """Test streaming with `reasoning=None`."""
    llm = ChatOllama(model=model, num_ctx=2**12, reasoning=None)
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
    # reasoning_content is only captured when reasoning=True
    assert "reasoning_content" not in result.additional_kwargs