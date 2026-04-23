def test_is_data_content_block() -> None:
    # Test all DataContentBlock types with various data fields

    # Image blocks
    assert is_data_content_block({"type": "image", "url": "https://..."})
    assert is_data_content_block(
        {
            "type": "image",
            "base64": "<base64 data>",
            "mime_type": "image/jpeg",
        }
    )

    # Video blocks
    assert is_data_content_block({"type": "video", "url": "https://video.mp4"})
    assert is_data_content_block(
        {
            "type": "video",
            "base64": "<base64 video>",
            "mime_type": "video/mp4",
        }
    )
    assert is_data_content_block({"type": "video", "file_id": "vid_123"})

    # Audio blocks
    assert is_data_content_block({"type": "audio", "url": "https://audio.mp3"})
    assert is_data_content_block(
        {
            "type": "audio",
            "base64": "<base64 audio>",
            "mime_type": "audio/mp3",
        }
    )
    assert is_data_content_block({"type": "audio", "file_id": "aud_123"})

    # Plain text blocks
    assert is_data_content_block({"type": "text-plain", "text": "document content"})
    assert is_data_content_block({"type": "text-plain", "url": "https://doc.txt"})
    assert is_data_content_block({"type": "text-plain", "file_id": "txt_123"})

    # File blocks
    assert is_data_content_block({"type": "file", "url": "https://file.pdf"})
    assert is_data_content_block(
        {
            "type": "file",
            "base64": "<base64 file>",
            "mime_type": "application/pdf",
        }
    )
    assert is_data_content_block({"type": "file", "file_id": "file_123"})

    # Blocks with additional metadata (should still be valid)
    assert is_data_content_block(
        {
            "type": "image",
            "base64": "<base64 data>",
            "mime_type": "image/jpeg",
            "cache_control": {"type": "ephemeral"},
        }
    )
    assert is_data_content_block(
        {
            "type": "image",
            "base64": "<base64 data>",
            "mime_type": "image/jpeg",
            "metadata": {"cache_control": {"type": "ephemeral"}},
        }
    )
    assert is_data_content_block(
        {
            "type": "image",
            "base64": "<base64 data>",
            "mime_type": "image/jpeg",
            "extras": "hi",
        }
    )

    # Invalid cases - wrong type
    assert not is_data_content_block({"type": "text", "text": "foo"})
    assert not is_data_content_block(
        {
            "type": "image_url",
            "image_url": {"url": "https://..."},
        }  # This is OpenAI Chat Completions
    )
    assert not is_data_content_block({"type": "tool_call", "name": "func", "args": {}})
    assert not is_data_content_block({"type": "invalid", "url": "something"})

    # Invalid cases - valid type but no data or `source_type` fields
    assert not is_data_content_block({"type": "image"})
    assert not is_data_content_block({"type": "video", "mime_type": "video/mp4"})
    assert not is_data_content_block({"type": "audio", "extras": {"key": "value"}})

    # Invalid cases - valid type but wrong data field name
    assert not is_data_content_block({"type": "image", "source": "<base64 data>"})
    assert not is_data_content_block({"type": "video", "data": "video_data"})

    # Edge cases - empty or missing values
    assert not is_data_content_block({})
    assert not is_data_content_block({"url": "https://..."})