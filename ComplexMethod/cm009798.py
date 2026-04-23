def test_convert_to_openai_data_block() -> None:
    # Chat completions
    # Image / url
    block = {
        "type": "image",
        "url": "https://example.com/test.png",
    }
    expected = {
        "type": "image_url",
        "image_url": {"url": "https://example.com/test.png"},
    }
    result = convert_to_openai_data_block(block)
    assert result == expected

    # Image / base64
    block = {
        "type": "image",
        "base64": "<base64 string>",
        "mime_type": "image/png",
    }
    expected = {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64,<base64 string>"},
    }
    result = convert_to_openai_data_block(block)
    assert result == expected

    # File / url
    block = {
        "type": "file",
        "url": "https://example.com/test.pdf",
    }
    with pytest.raises(ValueError, match="does not support"):
        result = convert_to_openai_data_block(block)

    # File / base64
    block = {
        "type": "file",
        "base64": "<base64 string>",
        "mime_type": "application/pdf",
        "filename": "test.pdf",
    }
    expected = {
        "type": "file",
        "file": {
            "file_data": "data:application/pdf;base64,<base64 string>",
            "filename": "test.pdf",
        },
    }
    result = convert_to_openai_data_block(block)
    assert result == expected

    # File / file ID
    block = {
        "type": "file",
        "file_id": "file-abc123",
    }
    expected = {"type": "file", "file": {"file_id": "file-abc123"}}
    result = convert_to_openai_data_block(block)
    assert result == expected

    # Audio / base64
    block = {
        "type": "audio",
        "base64": "<base64 string>",
        "mime_type": "audio/wav",
    }
    expected = {
        "type": "input_audio",
        "input_audio": {"data": "<base64 string>", "format": "wav"},
    }
    result = convert_to_openai_data_block(block)
    assert result == expected

    # Responses
    # Image / url
    block = {
        "type": "image",
        "url": "https://example.com/test.png",
    }
    expected = {"type": "input_image", "image_url": "https://example.com/test.png"}
    result = convert_to_openai_data_block(block, api="responses")
    assert result == expected

    # Image / base64
    block = {
        "type": "image",
        "base64": "<base64 string>",
        "mime_type": "image/png",
    }
    expected = {
        "type": "input_image",
        "image_url": "data:image/png;base64,<base64 string>",
    }
    result = convert_to_openai_data_block(block, api="responses")
    assert result == expected

    # File / url
    block = {
        "type": "file",
        "url": "https://example.com/test.pdf",
    }
    expected = {"type": "input_file", "file_url": "https://example.com/test.pdf"}

    # File / base64
    block = {
        "type": "file",
        "base64": "<base64 string>",
        "mime_type": "application/pdf",
        "filename": "test.pdf",
    }
    expected = {
        "type": "input_file",
        "file_data": "data:application/pdf;base64,<base64 string>",
        "filename": "test.pdf",
    }
    result = convert_to_openai_data_block(block, api="responses")
    assert result == expected

    # File / file ID
    block = {
        "type": "file",
        "file_id": "file-abc123",
    }
    expected = {"type": "input_file", "file_id": "file-abc123"}
    result = convert_to_openai_data_block(block, api="responses")
    assert result == expected