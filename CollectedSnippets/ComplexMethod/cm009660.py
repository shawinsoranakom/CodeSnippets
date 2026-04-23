def test_text_accessor() -> None:
    """Test that `message.text` property and `.text()` method return the same value."""
    human_msg = HumanMessage(content="Hello world")
    assert human_msg.text == "Hello world"
    assert human_msg.text == "Hello world"
    assert str(human_msg.text) == str(human_msg.text)

    system_msg = SystemMessage(content="You are a helpful assistant")
    assert system_msg.text == "You are a helpful assistant"
    assert system_msg.text == "You are a helpful assistant"
    assert str(system_msg.text) == str(system_msg.text)

    ai_msg = AIMessage(content="I can help you with that")
    assert ai_msg.text == "I can help you with that"
    assert ai_msg.text == "I can help you with that"
    assert str(ai_msg.text) == str(ai_msg.text)

    tool_msg = ToolMessage(content="Task completed", tool_call_id="tool_1")
    assert tool_msg.text == "Task completed"
    assert tool_msg.text == "Task completed"
    assert str(tool_msg.text) == str(tool_msg.text)

    complex_msg = HumanMessage(
        content=[{"type": "text", "text": "Hello "}, {"type": "text", "text": "world"}]
    )
    assert complex_msg.text == "Hello world"
    assert complex_msg.text == "Hello world"
    assert str(complex_msg.text) == str(complex_msg.text)

    mixed_msg = AIMessage(
        content=[
            {"type": "text", "text": "The answer is "},
            {"type": "tool_use", "name": "calculate", "input": {"x": 2}, "id": "1"},
            {"type": "text", "text": "42"},
        ]
    )
    assert mixed_msg.text == "The answer is 42"
    assert mixed_msg.text == "The answer is 42"
    assert str(mixed_msg.text) == str(mixed_msg.text)

    empty_msg = HumanMessage(content=[])
    assert empty_msg.text == ""
    assert empty_msg.text == ""
    assert str(empty_msg.text) == str(empty_msg.text)