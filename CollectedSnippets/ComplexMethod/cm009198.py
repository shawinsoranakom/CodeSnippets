def test_get_last_messages() -> None:
    messages: list[BaseMessage] = [HumanMessage("Hello")]
    last_messages, previous_response_id = _get_last_messages(messages)
    assert last_messages == [HumanMessage("Hello")]
    assert previous_response_id is None

    messages = [
        HumanMessage("Hello"),
        AIMessage("Hi there!", response_metadata={"id": "resp_123"}),
        HumanMessage("How are you?"),
    ]

    last_messages, previous_response_id = _get_last_messages(messages)
    assert last_messages == [HumanMessage("How are you?")]
    assert previous_response_id == "resp_123"

    messages = [
        HumanMessage("Hello"),
        AIMessage("Hi there!", response_metadata={"id": "resp_123"}),
        HumanMessage("How are you?"),
        AIMessage("Well thanks.", response_metadata={"id": "resp_456"}),
        HumanMessage("Great."),
    ]
    last_messages, previous_response_id = _get_last_messages(messages)
    assert last_messages == [HumanMessage("Great.")]
    assert previous_response_id == "resp_456"

    messages = [
        HumanMessage("Hello"),
        AIMessage("Hi there!", response_metadata={"id": "resp_123"}),
        HumanMessage("What's the weather?"),
        AIMessage(
            "",
            response_metadata={"id": "resp_456"},
            tool_calls=[
                {
                    "type": "tool_call",
                    "name": "get_weather",
                    "id": "call_123",
                    "args": {"location": "San Francisco"},
                }
            ],
        ),
        ToolMessage("It's sunny.", tool_call_id="call_123"),
    ]
    last_messages, previous_response_id = _get_last_messages(messages)
    assert last_messages == [ToolMessage("It's sunny.", tool_call_id="call_123")]
    assert previous_response_id == "resp_456"

    messages = [
        HumanMessage("Hello"),
        AIMessage("Hi there!", response_metadata={"id": "resp_123"}),
        HumanMessage("How are you?"),
        AIMessage("Well thanks.", response_metadata={"id": "resp_456"}),
        HumanMessage("Good."),
        HumanMessage("Great."),
    ]
    last_messages, previous_response_id = _get_last_messages(messages)
    assert last_messages == [HumanMessage("Good."), HumanMessage("Great.")]
    assert previous_response_id == "resp_456"

    messages = [
        HumanMessage("Hello"),
        AIMessage("Hi there!", response_metadata={"id": "resp_123"}),
    ]
    last_messages, response_id = _get_last_messages(messages)
    assert last_messages == []
    assert response_id == "resp_123"