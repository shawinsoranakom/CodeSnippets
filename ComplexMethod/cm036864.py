async def test_function_call_first_turn(client: OpenAI, model_name: str):
    tools = [
        {
            "type": "function",
            "name": "get_horoscope",
            "description": "Get today's horoscope for an astrological sign.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sign": {"type": "string"},
                },
                "required": ["sign"],
                "additionalProperties": False,
            },
            "strict": True,
        }
    ]

    response = await retry_for_tool_call(
        client,
        model=model_name,
        expected_tool_type="function_call",
        input="What is the horoscope for Aquarius today?",
        tools=tools,
        temperature=0.0,
    )
    assert response is not None
    assert response.status == "completed"

    output_types = [getattr(o, "type", None) for o in response.output]
    assert "reasoning" in output_types, (
        f"Expected reasoning in output, got: {output_types}"
    )
    assert has_output_type(response, "function_call"), (
        f"Expected function_call in output, got: {output_types}"
    )

    function_call = next(o for o in response.output if o.type == "function_call")
    assert function_call.name == "get_horoscope"
    assert function_call.call_id is not None

    args = json.loads(function_call.arguments)
    assert "sign" in args