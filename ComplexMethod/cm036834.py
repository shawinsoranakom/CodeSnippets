async def test_function_tool_use(
    client: openai.AsyncOpenAI,
    model_name: str,
    stream: bool,
    tool_choice: str | dict,
    enable_thinking: bool,
):
    if not stream:
        # Non-streaming test
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=model_name,
            tools=tools,
            tool_choice=tool_choice,
            extra_body={"chat_template_kwargs": {"enable_thinking": enable_thinking}},
        )
        if enable_thinking:
            assert chat_completion.choices[0].message.reasoning is not None
            assert chat_completion.choices[0].message.reasoning != ""
        assert chat_completion.choices[0].message.tool_calls is not None
        assert len(chat_completion.choices[0].message.tool_calls) > 0
    else:
        # Streaming test
        output_stream = await client.chat.completions.create(
            messages=messages,
            model=model_name,
            tools=tools,
            tool_choice=tool_choice,
            stream=True,
            extra_body={"chat_template_kwargs": {"enable_thinking": enable_thinking}},
        )

        output = []
        reasoning = []
        async for chunk in output_stream:
            if chunk.choices:
                if enable_thinking and getattr(
                    chunk.choices[0].delta, "reasoning", None
                ):
                    reasoning.append(chunk.choices[0].delta.reasoning)
                if chunk.choices[0].delta.tool_calls:
                    output.extend(chunk.choices[0].delta.tool_calls)

        assert len(output) > 0
        if enable_thinking:
            assert len(reasoning) > 0