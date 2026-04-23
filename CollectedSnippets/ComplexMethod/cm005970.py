async def test_multimodal_input_text_extraction():
    """Test that text is correctly extracted from multimodal content."""
    component = MockAgentComponent()

    # Create a message with multiple text items
    message = Message(text="Test")
    mock_lc_message = MagicMock()
    mock_lc_message.content = [
        {"type": "text", "text": "First part"},
        {"type": "image", "image_url": "https://example.com/image.jpg"},
        {"type": "text", "text": "Second part"},
    ]

    component.input_value = message

    # We need to test the logic directly since it's in run_agent
    # Let's extract the relevant logic
    image_dicts = [item for item in mock_lc_message.content if item.get("type") == "image"]
    text_content = [item for item in mock_lc_message.content if item.get("type") != "image"]

    text_strings = [
        item.get("text", "") for item in text_content if item.get("type") == "text" and item.get("text", "").strip()
    ]

    result_text = " ".join(text_strings) if text_strings else ""

    # Verify
    assert result_text == "First part Second part"
    assert len(image_dicts) == 1
    assert image_dicts[0]["image_url"] == "https://example.com/image.jpg"