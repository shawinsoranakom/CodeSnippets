def test_streaming_with_usage_metadata() -> None:
    """Test that streaming properly includes usage metadata."""
    chunk = {
        "id": "chatcmpl-123",
        "object": "chat.completion.chunk",
        "created": 1234567890,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "content": "Hello",
                },
                "finish_reason": None,
            }
        ],
        "x_groq": {
            "usage": {
                "prompt_tokens": 2006,
                "completion_tokens": 300,
                "total_tokens": 2306,
                "input_tokens_details": {"cached_tokens": 1920},
            }
        },
    }

    result = _convert_chunk_to_message_chunk(chunk, AIMessageChunk)

    assert isinstance(result, AIMessageChunk)
    assert result.content == "Hello"

    assert result.usage_metadata is not None
    assert isinstance(result.usage_metadata, dict)
    assert result.usage_metadata["input_tokens"] == 2006
    assert result.usage_metadata["output_tokens"] == 300
    assert result.usage_metadata["total_tokens"] == 2306

    assert "input_token_details" in result.usage_metadata
    assert result.usage_metadata["input_token_details"]["cache_read"] == 1920

    assert "output_token_details" not in result.usage_metadata