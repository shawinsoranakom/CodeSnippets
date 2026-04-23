async def test_parallel_tool_calls_with_results(
    client: openai.AsyncOpenAI, server_config: ServerConfig
):
    if not server_config.get("supports_parallel", True):
        pytest.skip(
            "The {} model doesn't support parallel tool calls".format(
                server_config["model"]
            )
        )

    models = await client.models.list()
    model_name: str = models.data[0].id
    chat_completion = await client.chat.completions.create(
        messages=MESSAGES_WITH_PARALLEL_TOOL_RESPONSE,
        temperature=0,
        max_completion_tokens=200,
        model=model_name,
        tools=[WEATHER_TOOL, SEARCH_TOOL],
        logprobs=False,
        seed=SEED,
    )

    choice = chat_completion.choices[0]

    assert choice.finish_reason != "tool_calls"  # "stop" or "length"
    assert choice.message.role == "assistant"
    assert choice.message.tool_calls is None or len(choice.message.tool_calls) == 0
    assert choice.message.content is not None
    assert "98" in choice.message.content  # Dallas temp in tool response
    assert "78" in choice.message.content  # Orlando temp in tool response

    stream = await client.chat.completions.create(
        messages=MESSAGES_WITH_PARALLEL_TOOL_RESPONSE,
        temperature=0,
        max_completion_tokens=200,
        model=model_name,
        tools=[WEATHER_TOOL, SEARCH_TOOL],
        logprobs=False,
        seed=SEED,
        stream=True,
    )

    chunks: list[str] = []
    finish_reason_count = 0
    role_sent: bool = False

    async for chunk in stream:
        delta = chunk.choices[0].delta

        if delta.role:
            assert not role_sent
            assert delta.role == "assistant"
            role_sent = True

        if delta.content:
            chunks.append(delta.content)

        if chunk.choices[0].finish_reason is not None:
            finish_reason_count += 1
            assert chunk.choices[0].finish_reason == choice.finish_reason

        assert not delta.tool_calls or len(delta.tool_calls) == 0

    assert role_sent
    assert finish_reason_count == 1
    assert len(chunks)
    assert "".join(chunks) == choice.message.content