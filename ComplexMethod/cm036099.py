async def test_tool_call_with_results(
    client: openai.AsyncOpenAI, server_config: ServerConfig
) -> None:
    _requires_tool_parser(server_config)

    models = await client.models.list()
    model_name: str = models.data[0].id

    # --- non-streaming ---
    chat_completion = await client.chat.completions.create(
        messages=ensure_system_prompt(MESSAGES_WITH_TOOL_RESPONSE, server_config),
        temperature=0,
        max_completion_tokens=100,
        model=model_name,
        tools=[WEATHER_TOOL, SEARCH_TOOL],
        logprobs=False,
        seed=SEED,
    )

    choice = chat_completion.choices[0]

    assert choice.finish_reason != "tool_calls"
    assert choice.message.tool_calls is None or len(choice.message.tool_calls) == 0
    assert choice.message.content is not None
    assert "98" in choice.message.content

    # --- streaming ---
    stream = await client.chat.completions.create(
        messages=ensure_system_prompt(MESSAGES_WITH_TOOL_RESPONSE, server_config),
        temperature=0,
        max_completion_tokens=100,
        model=model_name,
        tools=[WEATHER_TOOL, SEARCH_TOOL],
        logprobs=False,
        seed=SEED,
        stream=True,
    )

    result = await _collect_streamed_content(
        stream, expected_finish_reason=choice.finish_reason
    )

    assert result.role_sent
    assert result.finish_reason_count == 1
    assert len(result.chunks)
    assert "".join(result.chunks) == choice.message.content