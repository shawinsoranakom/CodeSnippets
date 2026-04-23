async def test_function_calling(client: OpenAI, model_name: str):
    tools = [GET_WEATHER_SCHEMA]

    response = await retry_for_tool_call(
        client,
        model=model_name,
        expected_tool_type="function_call",
        input="What's the weather like in Paris today?",
        tools=tools,
        temperature=0.0,
        extra_body={"request_id": "test_function_calling_non_resp"},
    )
    assert response.status == "completed"
    assert has_output_type(response, "function_call"), (
        f"Expected function_call in output, got: "
        f"{[getattr(o, 'type', None) for o in response.output]}"
    )

    tool_call = next(o for o in response.output if o.type == "function_call")
    args = json.loads(tool_call.arguments)
    result = call_function(tool_call.name, args)

    response_2 = await client.responses.create(
        model=model_name,
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
    assert response_2.output_text is not None

    # NOTE: chain-of-thought should be removed.
    response_3 = await client.responses.create(
        model=model_name,
        input="What's the weather like in Paris today?",
        tools=tools,
        previous_response_id=response_2.id,
        temperature=0.0,
    )
    assert response_3.status == "completed"
    assert response_3.output_text is not None