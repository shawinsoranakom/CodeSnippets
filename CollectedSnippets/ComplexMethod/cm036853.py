def test_mixed_input_types_with_function_calls():
    """Test parsing with mixed input types including function calls."""

    request_data = {
        "model": "gpt-oss",
        "input": [
            # Valid Message type
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "What's the weather?"}],
            },
            # Function call that should be parsed
            {
                "type": "function_call",
                "call_id": "fc_789",
                "name": "check_weather",
                "arguments": '{"location": "NYC"}',
            },
            # Another function call
            {
                "type": "function_call",
                "call_id": "fc_790",
                "name": "get_time",
                "arguments": "{}",
            },
        ],
    }

    request = ResponsesRequest(**request_data)

    # Verify mixed types are handled correctly
    assert len(request.input) == 3
    # First item should be validated as Message
    assert request.input[0]["type"] == "message"
    # Second item should be parsed to ResponseFunctionToolCall
    assert isinstance(request.input[1], ResponseFunctionToolCall)
    assert request.input[1].call_id == "fc_789"
    assert request.input[1].name == "check_weather"
    # Third item should also be parsed to ResponseFunctionToolCall
    assert isinstance(request.input[2], ResponseFunctionToolCall)
    assert request.input[2].call_id == "fc_790"
    assert request.input[2].name == "get_time"