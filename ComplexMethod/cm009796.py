def test_content_blocks_reasoning_extraction() -> None:
    """Test best-effort reasoning extraction from `additional_kwargs`."""
    message = AIMessage(
        content="The answer is 42.",
        additional_kwargs={"reasoning_content": "Let me think about this problem..."},
    )
    content_blocks = message.content_blocks
    assert len(content_blocks) == 2
    assert content_blocks[0]["type"] == "reasoning"
    assert content_blocks[0].get("reasoning") == "Let me think about this problem..."
    assert content_blocks[1]["type"] == "text"
    assert content_blocks[1]["text"] == "The answer is 42."

    # Test no reasoning extraction when no reasoning content
    message = AIMessage(
        content="The answer is 42.", additional_kwargs={"other_field": "some value"}
    )
    content_blocks = message.content_blocks
    assert len(content_blocks) == 1
    assert content_blocks[0]["type"] == "text"