async def test_reasoning_stream(model: str, use_async: bool) -> None:
    """Test streaming with `reasoning=True`."""
    llm = ChatOllama(model=model, num_ctx=2**12, reasoning=True)
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
    assert "reasoning_content" in result.additional_kwargs
    assert len(result.additional_kwargs["reasoning_content"]) > 0
    assert "<think>" not in result.content
    assert "</think>" not in result.content
    assert "<think>" not in result.additional_kwargs["reasoning_content"]
    assert "</think>" not in result.additional_kwargs["reasoning_content"]

    content_blocks = result.content_blocks
    assert content_blocks is not None
    assert len(content_blocks) > 0
    reasoning_blocks = [
        block for block in content_blocks if block.get("type") == "reasoning"
    ]
    assert len(reasoning_blocks) > 0