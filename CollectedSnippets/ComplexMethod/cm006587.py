def test_message_with_multiple_images(sample_image, langflow_cache_dir):
    """Test creating a message with multiple images."""
    # Create a second image in the cache directory
    flow_dir = langflow_cache_dir / "test_flow"
    second_image = flow_dir / "second_image.png"
    shutil.copy2(str(sample_image), str(second_image))

    # Use platformdirs for the real cache location
    real_cache_dir = Path(user_cache_dir("langflow")) / "test_flow"
    real_cache_dir.mkdir(parents=True, exist_ok=True)
    real_second_image = real_cache_dir / "second_image.png"
    shutil.copy2(str(sample_image), str(real_second_image))

    text = "Multiple images"
    message = Message(
        text=text,
        sender=MESSAGE_SENDER_USER,
        files=[f"test_flow/{sample_image.name}", f"test_flow/{second_image.name}"],
    )
    lc_message = message.to_lc_message()

    # The Message class now properly handles multimodal content
    assert isinstance(lc_message, HumanMessage)
    assert isinstance(lc_message.content, list)
    assert len(lc_message.content) == 3  # text + 2 images
    assert lc_message.content[0]["type"] == "text"
    assert lc_message.content[0]["text"] == text
    assert lc_message.content[1]["type"] == "image_url"
    assert lc_message.content[2]["type"] == "image_url"

    # Verify the message object has the files
    assert len(message.files) == 2
    assert f"test_flow/{sample_image.name}" in message.files
    assert f"test_flow/{second_image.name}" in message.files