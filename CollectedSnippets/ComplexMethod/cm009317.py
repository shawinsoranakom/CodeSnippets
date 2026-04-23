async def test_reasoning_invoke(model: str, use_async: bool) -> None:
    """Test invoke with `reasoning=True`."""
    llm = ChatOllama(model=model, num_ctx=2**12, reasoning=True)
    message = HumanMessage(content=SAMPLE)
    if use_async:
        result = await llm.ainvoke([message])
    else:
        result = llm.invoke([message])
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