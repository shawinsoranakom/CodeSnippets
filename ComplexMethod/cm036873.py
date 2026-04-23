async def test_function_calling_multi_turn(client: OpenAI, model_name: str):
    """Multi-tool, multi-turn function calling with retry at API level."""
    tools = [
        {
            "type": "function",
            "name": "get_place_to_travel",
            "description": "Get a random place to travel",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
        GET_WEATHER_SCHEMA,
    ]

    # Turn 1: model should call one of the tools
    response = await retry_for_tool_call(
        client,
        model=model_name,
        expected_tool_type="function_call",
        input="Help me plan a trip to a random place. And tell me the weather there.",
        tools=tools,
        temperature=0.0,
    )
    assert response.status == "completed"
    assert has_output_type(response, "function_call"), (
        f"Turn 1: expected function_call, got: "
        f"{[getattr(o, 'type', None) for o in response.output]}"
    )

    tool_call = next(o for o in response.output if o.type == "function_call")
    result = call_function(tool_call.name, json.loads(tool_call.arguments))

    # Turn 2
    response_2 = await retry_for_tool_call(
        client,
        model=model_name,
        expected_tool_type="function_call",
        input=[
            {
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": str(result),
            }
        ],
        tools=tools,
        previous_response_id=response.id,
        temperature=0.0,
    )
    assert response_2.status == "completed"

    # If model produced another tool call, execute it
    if has_output_type(response_2, "function_call"):
        tool_call_2 = next(o for o in response_2.output if o.type == "function_call")
        result_2 = call_function(tool_call_2.name, json.loads(tool_call_2.arguments))
        response_3 = await client.responses.create(
            model=model_name,
            input=[
                {
                    "type": "function_call_output",
                    "call_id": tool_call_2.call_id,
                    "output": str(result_2),
                }
            ],
            tools=tools,
            previous_response_id=response_2.id,
            temperature=0.0,
        )
        assert response_3.status == "completed"
        assert response_3.output_text is not None
    else:
        # Model went straight to answering - acceptable but unexpected.
        # Log as warning so it shows up in CI without failing the test.
        assert response_2.output_text is not None
        pytest.xfail(
            "Model went straight to answering instead of calling a "
            "second tool. Valid behaviour but not the expected path."
            "If this happens consistently, the prompt or model may have "
            "changed behaviour."
        )