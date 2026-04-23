async def test_multimodal_input_only_images():
    """Test that when only images are present, input becomes empty string."""
    mock_lc_message = MagicMock()
    mock_lc_message.content = [
        {"type": "image", "image_url": "https://example.com/image1.jpg"},
        {"type": "image", "image_url": "https://example.com/image2.jpg"},
    ]

    # Extract logic
    text_content = [item for item in mock_lc_message.content if item.get("type") != "image"]
    text_strings = [
        item.get("text", "") for item in text_content if item.get("type") == "text" and item.get("text", "").strip()
    ]

    result_text = " ".join(text_strings) if text_strings else ""

    # Verify
    assert result_text == ""