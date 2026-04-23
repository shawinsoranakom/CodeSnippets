def test_tool_outputs() -> None:
    messages = tool_example_to_messages(
        input="This is an example",
        tool_calls=[
            FakeCall(data="ToolCall1"),
        ],
        tool_outputs=["Output1"],
    )
    assert len(messages) == 3
    assert isinstance(messages[0], HumanMessage)
    assert isinstance(messages[1], AIMessage)
    assert isinstance(messages[2], ToolMessage)
    assert messages[1].additional_kwargs["tool_calls"] == [
        {
            "id": messages[2].tool_call_id,
            "type": "function",
            "function": {"name": "FakeCall", "arguments": '{"data":"ToolCall1"}'},
        },
    ]
    assert messages[2].content == "Output1"

    # Test final AI response
    messages = tool_example_to_messages(
        input="This is an example",
        tool_calls=[
            FakeCall(data="ToolCall1"),
        ],
        tool_outputs=["Output1"],
        ai_response="The output is Output1",
    )
    assert len(messages) == 4
    assert isinstance(messages[0], HumanMessage)
    assert isinstance(messages[1], AIMessage)
    assert isinstance(messages[2], ToolMessage)
    assert isinstance(messages[3], AIMessage)
    response = messages[3]
    assert response.content == "The output is Output1"
    assert not response.tool_calls