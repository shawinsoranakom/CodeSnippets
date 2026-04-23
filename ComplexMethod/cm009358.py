def test_chat_result_with_reasoning_tokens() -> None:
    """Test that _create_chat_result properly includes reasoning tokens."""
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
                    "content": "Test reasoning response",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 450,
            "total_tokens": 550,
            "output_tokens_details": {"reasoning_tokens": 200},
        },
    }

    result = llm._create_chat_result(mock_response, {})

    assert len(result.generations) == 1
    message = result.generations[0].message
    assert isinstance(message, AIMessage)
    assert message.content == "Test reasoning response"

    assert message.usage_metadata is not None
    assert isinstance(message.usage_metadata, dict)
    assert message.usage_metadata["input_tokens"] == 100
    assert message.usage_metadata["output_tokens"] == 450
    assert message.usage_metadata["total_tokens"] == 550

    assert "output_token_details" in message.usage_metadata
    assert message.usage_metadata["output_token_details"]["reasoning"] == 200

    assert "input_token_details" not in message.usage_metadata