def test__construct_responses_api_input_multiple_message_types() -> None:
    """Test conversion of a conversation with multiple message types."""
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        SystemMessage(
            content=[{"type": "text", "text": "You are a very helpful assistant!"}]
        ),
        HumanMessage(content="What's the weather in San Francisco?"),
        HumanMessage(
            content=[{"type": "text", "text": "What's the weather in San Francisco?"}]
        ),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "type": "tool_call",
                    "id": "call_123",
                    "name": "get_weather",
                    "args": {"location": "San Francisco"},
                }
            ],
        ),
        ToolMessage(
            content='{"temperature": 72, "conditions": "sunny"}',
            tool_call_id="call_123",
        ),
        AIMessage(content="The weather in San Francisco is 72°F and sunny."),
        AIMessage(
            content=[
                {
                    "type": "text",
                    "text": "The weather in San Francisco is 72°F and sunny.",
                }
            ]
        ),
    ]
    messages_copy = [m.model_copy(deep=True) for m in messages]

    result = _construct_responses_api_input(messages)

    assert len(result) == len(messages)

    # Check system message
    assert result[0]["type"] == "message"
    assert result[0]["role"] == "system"
    assert result[0]["content"] == "You are a helpful assistant."

    assert result[1]["type"] == "message"
    assert result[1]["role"] == "system"
    assert result[1]["content"] == [
        {"type": "input_text", "text": "You are a very helpful assistant!"}
    ]

    # Check human message
    assert result[2]["type"] == "message"
    assert result[2]["role"] == "user"
    assert result[2]["content"] == "What's the weather in San Francisco?"
    assert result[3]["type"] == "message"
    assert result[3]["role"] == "user"
    assert result[3]["content"] == [
        {"type": "input_text", "text": "What's the weather in San Francisco?"}
    ]

    # Check function call
    assert result[4]["type"] == "function_call"
    assert result[4]["name"] == "get_weather"
    assert result[4]["arguments"] == '{"location": "San Francisco"}'
    assert result[4]["call_id"] == "call_123"

    # Check function call output
    assert result[5]["type"] == "function_call_output"
    assert result[5]["output"] == '{"temperature": 72, "conditions": "sunny"}'
    assert result[5]["call_id"] == "call_123"

    assert result[6]["role"] == "assistant"
    assert result[6]["content"] == [
        {
            "type": "output_text",
            "text": "The weather in San Francisco is 72°F and sunny.",
            "annotations": [],
        }
    ]

    assert result[7]["role"] == "assistant"
    assert result[7]["content"] == [
        {
            "type": "output_text",
            "text": "The weather in San Francisco is 72°F and sunny.",
            "annotations": [],
        }
    ]

    # assert no mutation has occurred
    assert messages_copy == messages

    # Test dict messages
    llm = ChatOpenAI(model="o4-mini", use_responses_api=True)
    message_dicts: list = [
        {"role": "developer", "content": "This is a developer message."},
        {
            "role": "developer",
            "content": [{"type": "text", "text": "This is a developer message!"}],
        },
    ]
    payload = llm._get_request_payload(message_dicts)
    result = payload["input"]
    assert len(result) == 2
    assert result[0]["type"] == "message"
    assert result[0]["role"] == "developer"
    assert result[0]["content"] == "This is a developer message."
    assert result[1]["type"] == "message"
    assert result[1]["role"] == "developer"
    assert result[1]["content"] == [
        {"type": "input_text", "text": "This is a developer message!"}
    ]