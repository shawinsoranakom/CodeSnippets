def test_message_with_single_image(sample_image):
    """Test creating a message with text and an image."""
    text = "Check out this image"
    # Format the file path as expected: "flow_id/filename"
    file_path = f"test_flow/{sample_image.name}"
    message = Message(text=text, sender=MESSAGE_SENDER_USER, files=[file_path])
    lc_message = message.to_lc_message()

    # The Message class now properly handles multimodal content
    assert isinstance(lc_message, HumanMessage)
    assert isinstance(lc_message.content, list)
    assert len(lc_message.content) == 2  # text + image
    assert lc_message.content[0]["type"] == "text"
    assert lc_message.content[0]["text"] == text
    assert lc_message.content[1]["type"] == "image_url"
    assert "image_url" in lc_message.content[1]
    assert "url" in lc_message.content[1]["image_url"]
    assert lc_message.content[1]["image_url"]["url"].startswith("data:image/")

    # Verify the message object has files
    assert message.files == [file_path]