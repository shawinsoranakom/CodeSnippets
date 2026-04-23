def test_validator_handles_iterator_input():
    """Test that validator can handle ValidatorIterator input (Pydantic internal)."""

    # This test simulates when Pydantic passes a ValidatorIterator instead of a list
    # This happened with complex nested structures containing reasoning + function_call

    # Create test data that would normally be a list
    test_input_items = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Test"}],
        },
        {
            "type": "reasoning",
            "id": "rs_1",
            "summary": [{"type": "summary_text", "text": "Test reasoning"}],
            "content": [{"type": "reasoning_text", "text": "Test content"}],
        },
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "test_function",
            "arguments": '{"test": "value"}',
            "id": "fc_1",
        },
    ]

    # Mock data where input is an iterator (simulates Pydantic ValidatorIterator)
    mock_data = {
        "model": "test-model",
        "input": iter(test_input_items),  # Iterator instead of list
    }

    # This should NOT raise an error with the fixed validator
    try:
        request = ResponsesRequest(**mock_data)

        # Verify the validator processed the data correctly
        assert len(request.input) == 3

        # Verify function_call was converted to ResponseFunctionToolCall object
        function_call_item = None
        for item in request.input:
            if isinstance(item, ResponseFunctionToolCall):
                function_call_item = item
                break

        assert function_call_item is not None
        assert function_call_item.call_id == "call_1"
        assert function_call_item.name == "test_function"

    except Exception as e:
        pytest.fail(f"Validator should handle iterator input, but failed with: {e}")