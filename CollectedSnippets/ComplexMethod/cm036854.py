def test_mixed_function_call_and_output():
    """Test that function_call is parsed while function_call_output is preserved."""
    request_data = {
        "model": "gpt-oss",
        "input": [
            # This should be parsed to ResponseFunctionToolCall
            {
                "type": "function_call",
                "call_id": "fc_call_456",
                "name": "get_weather",
                "arguments": '{"location": "NYC"}',
            },
            # This should remain as dict
            {
                "type": "function_call_output",
                "call_id": "fc_call_456",
                "output": "NYC weather is 68°F with light rain",
            },
        ],
    }

    request = ResponsesRequest(**request_data)

    assert len(request.input) == 2

    # First item should be parsed to ResponseFunctionToolCall
    assert isinstance(request.input[0], ResponseFunctionToolCall)
    assert request.input[0].call_id == "fc_call_456"
    assert request.input[0].name == "get_weather"

    # Second item should remain as dict (FunctionCallOutput)
    assert isinstance(request.input[1], dict)
    assert request.input[1]["type"] == "function_call_output"
    assert request.input[1]["call_id"] == "fc_call_456"
    assert request.input[1]["output"] == "NYC weather is 68°F with light rain"