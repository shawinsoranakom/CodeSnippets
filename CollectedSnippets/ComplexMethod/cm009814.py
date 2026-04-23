def test_multiple_tool_calls() -> None:
    messages = tool_example_to_messages(
        input="This is an example",
        tool_calls=[
            FakeCall(data="ToolCall1"),
            FakeCall(data="ToolCall2"),
            FakeCall(data="ToolCall3"),
        ],
    )
    assert len(messages) == 5
    assert isinstance(messages[0], HumanMessage)
    assert isinstance(messages[1], AIMessage)
    assert isinstance(messages[2], ToolMessage)
    assert isinstance(messages[3], ToolMessage)
    assert isinstance(messages[4], ToolMessage)
    assert messages[1].additional_kwargs["tool_calls"] == [
        {
            "id": messages[2].tool_call_id,
            "type": "function",
            "function": {"name": "FakeCall", "arguments": '{"data":"ToolCall1"}'},
        },
        {
            "id": messages[3].tool_call_id,
            "type": "function",
            "function": {"name": "FakeCall", "arguments": '{"data":"ToolCall2"}'},
        },
        {
            "id": messages[4].tool_call_id,
            "type": "function",
            "function": {"name": "FakeCall", "arguments": '{"data":"ToolCall3"}'},
        },
    ]