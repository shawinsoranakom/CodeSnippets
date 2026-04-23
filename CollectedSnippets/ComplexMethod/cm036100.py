async def test_tool_call_parallel(
    client: openai.AsyncOpenAI, server_config: ServerConfig
) -> None:
    _requires_tool_parser(server_config)
    _requires_parallel(server_config)

    models = await client.models.list()
    model_name: str = models.data[0].id

    # --- non-streaming ---
    chat_completion = await client.chat.completions.create(
        messages=ensure_system_prompt(
            MESSAGES_ASKING_FOR_PARALLEL_TOOLS, server_config
        ),
        temperature=0,
        max_completion_tokens=200,
        model=model_name,
        tools=[WEATHER_TOOL],
        logprobs=False,
        seed=SEED,
    )

    choice = chat_completion.choices[0]
    tool_calls = choice.message.tool_calls

    assert choice.finish_reason == "tool_calls"
    assert tool_calls is not None and len(tool_calls) >= 2
    for tc in tool_calls:
        assert tc.type == "function"
        assert tc.function.name == "get_current_weather"
        assert isinstance(tc.function.arguments, str)
        parsed = json.loads(tc.function.arguments)
        assert "city" in parsed
        assert len(tc.id) == 9

    non_streaming_tool_calls = tool_calls

    # --- streaming ---
    stream = await client.chat.completions.create(
        messages=ensure_system_prompt(
            MESSAGES_ASKING_FOR_PARALLEL_TOOLS, server_config
        ),
        temperature=0,
        max_completion_tokens=200,
        model=model_name,
        tools=[WEATHER_TOOL],
        logprobs=False,
        seed=SEED,
        stream=True,
    )

    result = await _collect_streamed_parallel_tool_calls(stream)

    assert result.finish_reason_count == 1
    assert result.role_name == "assistant"
    assert len(result.function_names) >= 2
    assert all(name == "get_current_weather" for name in result.function_names)
    assert len(result.tool_call_ids) >= 2
    assert all(isinstance(tid, str) and len(tid) == 9 for tid in result.tool_call_ids)

    for args_str in result.function_args_strs:
        streamed_args = json.loads(args_str)
        assert "city" in streamed_args

    assert len(result.function_names) == len(non_streaming_tool_calls)