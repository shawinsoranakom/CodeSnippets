def test__construct_responses_api_input_ai_message_with_tool_calls() -> None:
    """Test that AI messages with tool calls are properly converted."""
    tool_calls = [
        {
            "id": "call_123",
            "name": "get_weather",
            "args": {"location": "San Francisco"},
            "type": "tool_call",
        }
    ]

    ai_message = AIMessage(
        content=[
            {
                "type": "function_call",
                "name": "get_weather",
                "arguments": '{"location": "San Francisco"}',
                "call_id": "call_123",
                "id": "fc_456",
            }
        ],
        tool_calls=tool_calls,
    )

    result = _construct_responses_api_input([ai_message])

    assert len(result) == 1
    assert result[0]["type"] == "function_call"
    assert result[0]["name"] == "get_weather"
    assert result[0]["arguments"] == '{"location": "San Francisco"}'
    assert result[0]["call_id"] == "call_123"
    assert result[0]["id"] == "fc_456"

    # Message with only tool calls attribute provided
    ai_message = AIMessage(content="", tool_calls=tool_calls)

    result = _construct_responses_api_input([ai_message])

    assert len(result) == 1
    assert result[0]["type"] == "function_call"
    assert result[0]["name"] == "get_weather"
    assert result[0]["arguments"] == '{"location": "San Francisco"}'
    assert result[0]["call_id"] == "call_123"
    assert "id" not in result[0]