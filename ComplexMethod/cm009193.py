def test__construct_responses_api_input_human_message_with_image_url_conversion() -> (
    None
):
    """Test that human messages with image_url blocks are properly converted."""
    messages: list = [
        HumanMessage(
            content=[
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "high",
                    },
                },
            ]
        )
    ]
    result = _construct_responses_api_input(messages)

    assert len(result) == 1
    assert result[0]["type"] == "message"
    assert result[0]["role"] == "user"
    assert isinstance(result[0]["content"], list)
    assert len(result[0]["content"]) == 2

    # Check text block conversion
    assert result[0]["content"][0]["type"] == "input_text"
    assert result[0]["content"][0]["text"] == "What's in this image?"

    # Check image block conversion
    assert result[0]["content"][1]["type"] == "input_image"
    assert result[0]["content"][1]["image_url"] == "https://example.com/image.jpg"
    assert result[0]["content"][1]["detail"] == "high"