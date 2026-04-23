async def test_parallel_tool_calls_false(client: openai.AsyncOpenAI):
    """
    Ensure only one tool call is returned when parallel_tool_calls is False.
    """

    models = await client.models.list()
    model_name: str = models.data[0].id
    chat_completion = await client.chat.completions.create(
        messages=MESSAGES_ASKING_FOR_PARALLEL_TOOLS,
        temperature=0,
        max_completion_tokens=200,
        model=model_name,
        tools=[WEATHER_TOOL, SEARCH_TOOL],
        logprobs=False,
        seed=SEED,
        parallel_tool_calls=False,
    )

    stop_reason = chat_completion.choices[0].finish_reason
    non_streamed_tool_calls = chat_completion.choices[0].message.tool_calls

    # make sure only 1 tool call is present
    assert len(non_streamed_tool_calls) == 1
    assert stop_reason == "tool_calls"

    # make the same request, streaming
    stream = await client.chat.completions.create(
        model=model_name,
        messages=MESSAGES_ASKING_FOR_PARALLEL_TOOLS,
        temperature=0,
        max_completion_tokens=200,
        tools=[WEATHER_TOOL, SEARCH_TOOL],
        logprobs=False,
        seed=SEED,
        parallel_tool_calls=False,
        stream=True,
    )

    finish_reason_count: int = 0
    tool_call_id_count: int = 0

    async for chunk in stream:
        # if there's a finish reason make sure it's tools
        if chunk.choices[0].finish_reason:
            finish_reason_count += 1
            assert chunk.choices[0].finish_reason == "tool_calls"

        streamed_tool_calls = chunk.choices[0].delta.tool_calls
        if streamed_tool_calls and len(streamed_tool_calls) > 0:
            tool_call = streamed_tool_calls[0]
            if tool_call.id:
                tool_call_id_count += 1

    # make sure only 1 streaming tool call is present
    assert tool_call_id_count == 1
    assert finish_reason_count == 1