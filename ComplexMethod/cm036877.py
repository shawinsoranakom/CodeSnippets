async def test_function_call_with_previous_input_messages(
    client: OpenAI, model_name: str
):
    """Multi-turn function calling using previous_input_messages."""
    tools = [
        {
            "type": "function",
            "name": "get_horoscope",
            "description": "Get today's horoscope for an astrological sign.",
            "parameters": {
                "type": "object",
                "properties": {"sign": {"type": "string"}},
                "required": ["sign"],
                "additionalProperties": False,
            },
            "strict": True,
        }
    ]

    # Step 1: Get a function call from the model
    response = await retry_for_tool_call(
        client,
        model=model_name,
        expected_tool_type="function_call",
        input="What is the horoscope for Aquarius today?",
        tools=tools,
        temperature=0.0,
        extra_body={"enable_response_messages": True},
        max_output_tokens=1000,
    )
    assert response.status == "completed"

    function_call = next(
        (item for item in response.output if item.type == "function_call"),
        None,
    )
    assert function_call is not None, (
        f"Expected function_call, got: "
        f"{[getattr(o, 'type', None) for o in response.output]}"
    )
    assert function_call.name == "get_horoscope"

    args = json.loads(function_call.arguments)
    result = call_function(function_call.name, args)

    # Step 2: Build full conversation history
    previous_messages = (
        response.input_messages
        + response.output_messages
        + [
            {
                "role": "tool",
                "name": "functions.get_horoscope",
                "content": [{"type": "text", "text": str(result)}],
            }
        ]
    )

    # Step 3: Second call with previous_input_messages
    response_2 = await client.responses.create(
        model=model_name,
        tools=tools,
        temperature=0.0,
        input="Now tell me the horoscope based on the tool result.",
        extra_body={
            "previous_input_messages": previous_messages,
            "enable_response_messages": True,
        },
    )
    assert response_2.status == "completed"
    assert response_2.output_text is not None

    # Verify exactly 1 system, 1 developer, 1 tool message
    num_system = 0
    num_developer = 0
    num_tool = 0
    for message in (
        Message.from_dict(msg_dict) for msg_dict in response_2.input_messages
    ):
        role = message.author.role
        if role == "system":
            num_system += 1
        elif role == "developer":
            num_developer += 1
        elif role == "tool":
            num_tool += 1
    assert num_system == 1, f"Expected 1 system message, got {num_system}"
    assert num_developer == 1, f"Expected 1 developer message, got {num_developer}"
    assert num_tool == 1, f"Expected 1 tool message, got {num_tool}"

    output_text = response_2.output_text.lower()
    assert any(kw in output_text for kw in ["aquarius", "otter", "tuesday"]), (
        f"Expected horoscope-related content, got: {response_2.output_text}"
    )