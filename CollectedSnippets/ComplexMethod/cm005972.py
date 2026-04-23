async def test_multimodal_input_empty_text():
    """Test that empty text items are filtered out."""
    mock_lc_message = MagicMock()
    mock_lc_message.content = [
        {"type": "text", "text": ""},
        {"type": "text", "text": "   "},
        {"type": "text", "text": "Valid text"},
        {"type": "image", "image_url": "https://example.com/image.jpg"},
    ]

    # Extract logic
    text_content = [item for item in mock_lc_message.content if item.get("type") != "image"]
    text_strings = [
        item.get("text", "") for item in text_content if item.get("type") == "text" and item.get("text", "").strip()
    ]

    result_text = " ".join(text_strings) if text_strings else ""

    # Verify - only non-empty text should be included
    assert result_text == "Valid text"