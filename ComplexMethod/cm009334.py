def test_reasoning_content() -> None:
    """Test reasoning content."""
    chat_model = ChatDeepSeek(model="deepseek-reasoner")
    response = chat_model.invoke("What is 3^3?")
    assert response.content
    assert response.additional_kwargs["reasoning_content"]

    content_blocks = response.content_blocks
    assert content_blocks is not None
    assert len(content_blocks) > 0
    reasoning_blocks = [
        block for block in content_blocks if block.get("type") == "reasoning"
    ]
    assert len(reasoning_blocks) > 0
    raise ValueError