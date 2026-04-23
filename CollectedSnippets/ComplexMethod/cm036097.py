async def test_tool_call_none_with_tools(
    client: openai.AsyncOpenAI, server_config: ServerConfig
) -> None:
    _requires_tool_parser(server_config)

    models = await client.models.list()
    model_name: str = models.data[0].id

    # --- non-streaming ---
    chat_completion = await client.chat.completions.create(
        messages=ensure_system_prompt(MESSAGES_ASKING_FOR_TOOLS, server_config),
        temperature=0,
        max_completion_tokens=100,
        model=model_name,
        tools=[WEATHER_TOOL],
        tool_choice="none",
        logprobs=False,
        seed=SEED,
    )

    choice = chat_completion.choices[0]

    assert choice.finish_reason != "tool_calls"
    assert choice.message.tool_calls is None or len(choice.message.tool_calls) == 0
    assert choice.message.content is not None
    # Without grammar enforcement, pre-v11 models may still emit [TOOL_CALLS]
    if not _is_pre_v11(server_config):
        assert "[TOOL_CALLS]" not in choice.message.content

    non_streaming_content = choice.message.content

    # --- streaming ---
    stream = await client.chat.completions.create(
        messages=ensure_system_prompt(MESSAGES_ASKING_FOR_TOOLS, server_config),
        temperature=0,
        max_completion_tokens=100,
        model=model_name,
        tools=[WEATHER_TOOL],
        tool_choice="none",
        logprobs=False,
        seed=SEED,
        stream=True,
    )

    # Pre-v11 models lack grammar enforcement, so the model may still
    # emit tool calls even with tool_choice="none".
    pre_v11 = _is_pre_v11(server_config)
    result = await _collect_streamed_content(stream, no_tool_calls=not pre_v11)

    assert result.finish_reason_count == 1
    if not pre_v11:
        assert result.finish_reason != "tool_calls"
    streamed_content = "".join(result.chunks)
    if not pre_v11:
        assert "[TOOL_CALLS]" not in streamed_content
        assert streamed_content == non_streaming_content