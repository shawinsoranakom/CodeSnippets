def test__construct_responses_api_input_human_message_with_text_blocks_conversion() -> (
    None
):
    """Test that human messages with text blocks are properly converted."""
    messages: list = [
        HumanMessage(content=[{"type": "text", "text": "What's in this image?"}])
    ]
    result = _construct_responses_api_input(messages)

    assert len(result) == 1
    assert result[0]["type"] == "message"
    assert result[0]["role"] == "user"
    assert isinstance(result[0]["content"], list)
    assert len(result[0]["content"]) == 1
    assert result[0]["content"][0]["type"] == "input_text"
    assert result[0]["content"][0]["text"] == "What's in this image?"