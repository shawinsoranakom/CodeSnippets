def test_message_with_image_object_direct():
    """Test that Message properly handles Image objects after model_post_init.

    This test verifies the fix for the bug where get_file_content_dicts() would fail
    when self.files contained Image objects instead of string paths.
    """
    # Create a temporary image file
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image_content = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
        )
        tmp.write(image_content)
        tmp_path = tmp.name

    try:
        # Create message with absolute path
        message = Message(text="Test with absolute path", sender=MESSAGE_SENDER_USER, files=[tmp_path])

        # After model_post_init, files should contain Image objects
        from lfx.schema.image import Image

        assert len(message.files) == 1
        assert isinstance(message.files[0], Image)
        assert message.files[0].path == tmp_path

        # Convert to LangChain message should work
        lc_message = message.to_lc_message()
        assert isinstance(lc_message, HumanMessage)
        assert isinstance(lc_message.content, list)
        assert len(lc_message.content) == 2  # text + image
        assert lc_message.content[0]["type"] == "text"
        assert lc_message.content[1]["type"] == "image_url"
        assert "url" in lc_message.content[1]["image_url"]
    finally:
        # Clean up
        Path(tmp_path).unlink(missing_ok=True)