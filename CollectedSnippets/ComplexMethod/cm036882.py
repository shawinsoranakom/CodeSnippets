async def test_function_calling_with_streaming_expected_arguments(
    client: openai.AsyncOpenAI, model_name: str
):
    tools = [
        {
            "type": "function",
            "name": "get_weather",
            "description": "Get current temperature for provided location in celsius.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                },
                "required": ["location"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "get_time",
            "description": "Get current local time for provided location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                },
                "required": ["location"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    ]

    stream_response = await client.responses.create(
        model=model_name,
        input=(
            "Use tools only. Call get_weather for Berlin and get_time for Tokyo. "
            "Do not answer directly."
        ),
        tools=tools,
        stream=True,
    )

    tool_call_items = {}
    arguments_done_events = {}
    completed_events = {}
    async for event in stream_response:
        if (
            event.type == "response.output_item.added"
            and event.item.type == "function_call"
        ):
            tool_call_items[event.output_index] = event.item
        elif event.type == "response.function_call_arguments.delta":
            tool_call_item = tool_call_items[event.output_index]
            tool_call_item.arguments += event.delta
        elif event.type == "response.function_call_arguments.done":
            arguments_done_events[event.output_index] = event
        elif (
            event.type == "response.output_item.done"
            and event.item.type == "function_call"
        ):
            completed_events[event.output_index] = event
    assert len(tool_call_items) >= 2
    assert len(arguments_done_events) >= 2
    assert len(completed_events) >= 2

    tool_calls_by_name = {
        event.item.name: (
            tool_call_items[output_index],
            arguments_done_events[output_index],
            event.item,
        )
        for output_index, event in completed_events.items()
    }
    assert {"get_weather", "get_time"}.issubset(tool_calls_by_name)
    for added_item, arguments_done_event, completed_item in tool_calls_by_name.values():
        assert added_item.type == "function_call"
        assert added_item.arguments == arguments_done_event.arguments
        assert added_item.arguments == completed_item.arguments
        assert added_item.name == arguments_done_event.name
        assert added_item.name == completed_item.name
        args = json.loads(added_item.arguments)
        assert "location" in args
        assert args["location"] is not None