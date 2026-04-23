async def test_function_calling_with_stream(client: OpenAI, model_name: str):
    """Function calling via streaming, with retry for non-determinism."""
    tools = [GET_WEATHER_SCHEMA]
    input_list = [
        {"role": "user", "content": "What's the weather like in Paris today?"},
    ]

    def _has_function_call(evts: list) -> bool:
        return any(
            getattr(e, "type", "") == "response.output_item.added"
            and getattr(getattr(e, "item", None), "type", None) == "function_call"
            for e in evts
        )

    events = await retry_streaming_for(
        client,
        model=model_name,
        validate_events=_has_function_call,
        input=input_list,
        tools=tools,
        temperature=0.0,
    )

    # Parse tool calls from events
    final_tool_calls: dict[int, Any] = {}
    for event in events:
        if event.type == "response.output_item.added":
            if getattr(event.item, "type", None) == "function_call":
                final_tool_calls[event.output_index] = event.item
        elif event.type == "response.function_call_arguments.delta":
            tc = final_tool_calls.get(event.output_index)
            if tc:
                tc.arguments += event.delta
        elif event.type == "response.function_call_arguments.done":
            tc = final_tool_calls.get(event.output_index)
            if tc:
                assert event.arguments == tc.arguments

    # Find get_weather call
    tool_call = None
    result = None
    for tc in final_tool_calls.values():
        if getattr(tc, "type", None) == "function_call" and tc.name == "get_weather":
            args = json.loads(tc.arguments)
            result = call_function(tc.name, args)
            tool_call = tc
            input_list.append(tc)
            break

    assert tool_call is not None, (
        "Expected model to call 'get_weather', "
        f"but got: {[getattr(tc, 'name', None) for tc in final_tool_calls.values()]}"
    )

    # Second turn with the tool result
    response = await client.responses.create(
        model=model_name,
        input=input_list
        + [
            {
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": str(result),
            }
        ],
        tools=tools,
        stream=True,
        temperature=0.0,
    )
    async for event in response:
        # check that no function call events in the stream
        assert event.type != "response.function_call_arguments.delta"
        assert event.type != "response.function_call_arguments.done"
        # check that the response contains output text
        if event.type == "response.completed":
            assert len(event.response.output) > 0
            assert event.response.output_text is not None