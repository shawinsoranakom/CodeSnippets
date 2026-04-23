def test_chat_result_with_usage_metadata() -> None:
    """Test that _create_chat_result properly includes usage metadata."""
    llm = ChatGroq(model="test-model")

    mock_response = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 2006,
            "completion_tokens": 300,
            "total_tokens": 2306,
            "input_tokens_details": {"cached_tokens": 1920},
        },
    }

    result = llm._create_chat_result(mock_response, {})

    assert len(result.generations) == 1
    message = result.generations[0].message
    assert isinstance(message, AIMessage)
    assert message.content == "Test response"

    assert message.usage_metadata is not None
    assert isinstance(message.usage_metadata, dict)
    assert message.usage_metadata["input_tokens"] == 2006
    assert message.usage_metadata["output_tokens"] == 300
    assert message.usage_metadata["total_tokens"] == 2306

    assert "input_token_details" in message.usage_metadata
    assert message.usage_metadata["input_token_details"]["cache_read"] == 1920

    assert "output_token_details" not in message.usage_metadata