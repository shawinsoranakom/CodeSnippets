def test_reasoning_content_streaming() -> None:
    """Test reasoning content with streaming."""
    chat_model = ChatDeepSeek(model="deepseek-reasoner")
    full: BaseMessageChunk | None = None
    for chunk in chat_model.stream("What is 3^3?"):
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert full.additional_kwargs["reasoning_content"]

    content_blocks = full.content_blocks
    assert content_blocks is not None
    assert len(content_blocks) > 0
    reasoning_blocks = [
        block for block in content_blocks if block.get("type") == "reasoning"
    ]
    assert len(reasoning_blocks) > 0