async def test_tool_call_auto_or_required(
    client: openai.AsyncOpenAI,
    server_config: ServerConfig,
    tools: list,
    tool_choice: object,
    streaming_id_len_pre_v11: int,
) -> None:
    _requires_tool_parser(server_config)

    models = await client.models.list()
    model_name: str = models.data[0].id

    create_kwargs: dict = {
        "messages": ensure_system_prompt(MESSAGES_ASKING_FOR_TOOLS, server_config),
        "temperature": 0,
        "max_completion_tokens": 100,
        "model": model_name,
        "tools": tools,
        "logprobs": False,
        "seed": SEED,
    }
    if tool_choice is not _NOT_SET:
        create_kwargs["tool_choice"] = tool_choice

    # --- non-streaming ---
    chat_completion = await client.chat.completions.create(**create_kwargs)

    choice = chat_completion.choices[0]
    tool_calls = choice.message.tool_calls

    assert choice.finish_reason == "tool_calls"
    assert tool_calls is not None and len(tool_calls) >= 1
    assert tool_calls[0].function.name == "get_current_weather"
    parsed_arguments = json.loads(tool_calls[0].function.arguments)
    assert "city" in parsed_arguments
    assert len(tool_calls[0].id) == 9

    # --- streaming ---
    stream = await client.chat.completions.create(**create_kwargs, stream=True)

    result = await _collect_streamed_tool_call(stream)

    assert result.finish_reason_count == 1
    assert result.role_name == "assistant"
    assert result.function_name == "get_current_weather"
    streamed_args = json.loads(result.function_args_str)
    assert isinstance(result.tool_call_id, str)
    if _is_pre_v11(server_config):
        assert len(result.tool_call_id) == streaming_id_len_pre_v11
    else:
        assert len(result.tool_call_id) == 9
    assert parsed_arguments == streamed_args