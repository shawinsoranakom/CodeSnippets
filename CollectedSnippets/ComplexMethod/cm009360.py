def test_chat_result_backward_compatibility() -> None:
    """Test that responses without new fields still work."""
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
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
    }

    result = llm._create_chat_result(mock_response, {})

    assert len(result.generations) == 1
    message = result.generations[0].message
    assert isinstance(message, AIMessage)

    assert message.usage_metadata is not None
    assert message.usage_metadata["input_tokens"] == 100
    assert message.usage_metadata["output_tokens"] == 50
    assert message.usage_metadata["total_tokens"] == 150

    assert "input_token_details" not in message.usage_metadata
    assert "output_token_details" not in message.usage_metadata