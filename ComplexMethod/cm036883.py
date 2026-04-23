async def test_function_calling_with_streaming_types(
    client: openai.AsyncOpenAI, model_name: str
):
    # this links the "done" type with the "start" type
    # so every "done" type should have a corresponding "start" type
    # and every open block should be closed by the end of the stream
    pairs_of_event_types = {
        "response.completed": "response.created",
        "response.output_item.done": "response.output_item.added",
        "response.output_text.done": "response.output_text.delta",
        "response.content_part.done": "response.content_part.added",
        "response.reasoning_text.done": "response.reasoning_text.delta",
        "response.reasoning_part.done": "response.reasoning_part.added",
        "response.function_call_arguments.done": "response.function_call_arguments.delta",  # noqa
    }

    input_list = [
        {
            "role": "user",
            "content": "Can you tell me what the current weather is in Berlin?",
        }
    ]
    stream_response = await client.responses.create(
        model=model_name,
        input=input_list,
        tools=tools,
        stream=True,
    )

    stack_of_event_types = []
    async for event in stream_response:
        if event.type == "response.created":
            stack_of_event_types.append(event.type)
        elif event.type == "response.completed":
            assert stack_of_event_types[-1] == pairs_of_event_types[event.type]
            stack_of_event_types.pop()
        if event.type.endswith("added"):
            stack_of_event_types.append(event.type)
        elif event.type.endswith("delta"):
            if stack_of_event_types[-1] == event.type:
                continue
            stack_of_event_types.append(event.type)
        elif event.type.endswith("done"):
            assert stack_of_event_types[-1] == pairs_of_event_types[event.type]
            stack_of_event_types.pop()
    assert len(stack_of_event_types) == 0