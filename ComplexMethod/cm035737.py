def test_message_tool_call_serialization():
    """Test that tool calls are properly serialized into dicts for token counting."""
    # Create a tool call
    tool_call = ChatCompletionMessageToolCall(
        id='call_123',
        type='function',
        function={'name': 'test_function', 'arguments': '{"arg1": "value1"}'},
    )

    # Create a message with the tool call
    message = Message(
        role='assistant',
        content=[TextContent(text='Test message')],
        tool_calls=[tool_call],
    )

    # Serialize the message
    serialized = message.model_dump()

    # Check that tool calls are properly serialized
    assert 'tool_calls' in serialized
    assert isinstance(serialized['tool_calls'], list)
    assert len(serialized['tool_calls']) == 1

    tool_call_dict = serialized['tool_calls'][0]
    assert isinstance(tool_call_dict, dict)
    assert tool_call_dict['id'] == 'call_123'
    assert tool_call_dict['type'] == 'function'
    assert tool_call_dict['function']['name'] == 'test_function'
    assert tool_call_dict['function']['arguments'] == '{"arg1": "value1"}'