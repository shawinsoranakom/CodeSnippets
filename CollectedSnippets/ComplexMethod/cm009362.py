def test_streaming_with_reasoning_tokens() -> None:
    """Test that streaming properly includes reasoning tokens in usage metadata."""
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
                "prompt_tokens": 100,
                "completion_tokens": 450,
                "total_tokens": 550,
                "output_tokens_details": {"reasoning_tokens": 200},
            }
        },
    }

    result = _convert_chunk_to_message_chunk(chunk, AIMessageChunk)

    assert isinstance(result, AIMessageChunk)
    assert result.content == "Hello"

    assert result.usage_metadata is not None
    assert isinstance(result.usage_metadata, dict)
    assert result.usage_metadata["input_tokens"] == 100
    assert result.usage_metadata["output_tokens"] == 450
    assert result.usage_metadata["total_tokens"] == 550

    assert "output_token_details" in result.usage_metadata
    assert result.usage_metadata["output_token_details"]["reasoning"] == 200

    assert "input_token_details" not in result.usage_metadata