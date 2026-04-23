def test__construct_responses_api_input_ai_message_with_tool_calls_and_content() -> (
    None
):
    """Test that AI messages with both tool calls and content are properly converted."""
    tool_calls = [
        {
            "id": "call_123",
            "name": "get_weather",
            "args": {"location": "San Francisco"},
            "type": "tool_call",
        }
    ]

    # Content blocks
    ai_message = AIMessage(
        content=[
            {"type": "text", "text": "I'll check the weather for you."},
            {
                "type": "function_call",
                "name": "get_weather",
                "arguments": '{"location": "San Francisco"}',
                "call_id": "call_123",
                "id": "fc_456",
            },
        ],
        tool_calls=tool_calls,
    )

    result = _construct_responses_api_input([ai_message])

    assert len(result) == 2

    assert result[0]["role"] == "assistant"
    assert result[0]["content"] == [
        {
            "type": "output_text",
            "text": "I'll check the weather for you.",
            "annotations": [],
        }
    ]

    assert result[1]["type"] == "function_call"
    assert result[1]["name"] == "get_weather"
    assert result[1]["arguments"] == '{"location": "San Francisco"}'
    assert result[1]["call_id"] == "call_123"
    assert result[1]["id"] == "fc_456"

    # String content
    ai_message = AIMessage(
        content="I'll check the weather for you.", tool_calls=tool_calls
    )

    result = _construct_responses_api_input([ai_message])

    assert len(result) == 2

    assert result[0]["role"] == "assistant"
    assert result[0]["content"] == [
        {
            "type": "output_text",
            "text": "I'll check the weather for you.",
            "annotations": [],
        }
    ]

    assert result[1]["type"] == "function_call"
    assert result[1]["name"] == "get_weather"
    assert result[1]["arguments"] == '{"location": "San Francisco"}'
    assert result[1]["call_id"] == "call_123"
    assert "id" not in result[1]