async def test_parallel_tool_calls(
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
        messages=MESSAGES_ASKING_FOR_PARALLEL_TOOLS,
        temperature=0,
        max_completion_tokens=200,
        model=model_name,
        tools=[WEATHER_TOOL, SEARCH_TOOL],
        logprobs=False,
        seed=SEED,
    )

    choice = chat_completion.choices[0]
    stop_reason = chat_completion.choices[0].finish_reason
    non_streamed_tool_calls = chat_completion.choices[0].message.tool_calls

    # make sure 2 tool calls are present
    assert choice.message.role == "assistant"
    assert non_streamed_tool_calls is not None
    assert len(non_streamed_tool_calls) == 2

    for tool_call in non_streamed_tool_calls:
        # make sure the tool includes a function and ID
        assert tool_call.type == "function"
        assert tool_call.function is not None
        assert isinstance(tool_call.id, str)
        assert len(tool_call.id) >= 9

        # make sure the weather tool was called correctly
        assert tool_call.function.name == WEATHER_TOOL["function"]["name"]
        assert isinstance(tool_call.function.arguments, str)

        parsed_arguments = json.loads(tool_call.function.arguments)
        assert isinstance(parsed_arguments, dict)
        assert isinstance(parsed_arguments.get("city"), str)
        assert isinstance(parsed_arguments.get("state"), str)

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
        stream=True,
    )

    role_name: str | None = None
    finish_reason_count: int = 0

    tool_call_names: list[str] = []
    tool_call_args: list[str] = []
    tool_call_idx: int = -1
    tool_call_id_count: int = 0

    async for chunk in stream:
        # if there's a finish reason make sure it's tools
        if chunk.choices[0].finish_reason:
            finish_reason_count += 1
            assert chunk.choices[0].finish_reason == "tool_calls"

        # if a role is being streamed make sure it wasn't already set to
        # something else
        if chunk.choices[0].delta.role:
            assert not role_name or role_name == "assistant"
            role_name = "assistant"

        # if a tool call is streamed make sure there's exactly one
        # (based on the request parameters
        streamed_tool_calls = chunk.choices[0].delta.tool_calls

        if streamed_tool_calls and len(streamed_tool_calls) > 0:
            # make sure only one diff is present - correct even for parallel
            assert len(streamed_tool_calls) == 1
            tool_call = streamed_tool_calls[0]

            # if a new tool is being called, set up empty arguments
            if tool_call.index != tool_call_idx:
                tool_call_idx = tool_call.index
                tool_call_args.append("")

            # if a tool call ID is streamed, make sure one hasn't been already
            if tool_call.id:
                tool_call_id_count += 1
                assert isinstance(tool_call.id, str) and (len(tool_call.id) >= 9)

            # if parts of the function start being streamed
            if tool_call.function:
                # if the function name is defined, set it. it should be streamed
                # IN ENTIRETY, exactly one time.
                if tool_call.function.name:
                    assert isinstance(tool_call.function.name, str)
                    tool_call_names.append(tool_call.function.name)

                if tool_call.function.arguments:
                    # make sure they're a string and then add them to the list
                    assert isinstance(tool_call.function.arguments, str)

                    tool_call_args[tool_call.index] += tool_call.function.arguments

    assert finish_reason_count == 1
    assert role_name == "assistant"

    assert len(non_streamed_tool_calls) == len(tool_call_names) == len(tool_call_args)

    for i in range(2):
        assert non_streamed_tool_calls[i].function.name == tool_call_names[i]
        streamed_args = json.loads(tool_call_args[i])
        non_streamed_args = json.loads(non_streamed_tool_calls[i].function.arguments)
        assert streamed_args == non_streamed_args