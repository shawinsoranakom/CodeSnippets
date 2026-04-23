async def test_chat_without_tools(
    client: openai.AsyncOpenAI, server_config: ServerConfig
) -> None:
    models = await client.models.list()
    model_name: str = models.data[0].id

    # --- non-streaming ---
    chat_completion = await client.chat.completions.create(
        messages=ensure_system_prompt(MESSAGES_WITHOUT_TOOLS, server_config),
        temperature=0,
        max_completion_tokens=150,
        model=model_name,
        logprobs=False,
        seed=SEED,
    )

    choice = chat_completion.choices[0]
    output_text = choice.message.content

    assert output_text is not None and len(output_text) > 0
    assert choice.finish_reason != "tool_calls"
    assert choice.message.tool_calls is None or len(choice.message.tool_calls) == 0

    # --- streaming ---
    stream = await client.chat.completions.create(
        messages=ensure_system_prompt(MESSAGES_WITHOUT_TOOLS, server_config),
        temperature=0,
        max_completion_tokens=150,
        model=model_name,
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
    assert "".join(result.chunks) == output_text