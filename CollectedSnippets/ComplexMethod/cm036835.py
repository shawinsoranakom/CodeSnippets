async def test_tool_id_kimi_k2(
    k2_client: openai.AsyncOpenAI, model_name: str, stream: bool, tool_choice: str
):
    if not stream:
        # Non-streaming test
        chat_completion = await k2_client.chat.completions.create(
            messages=messages, model=model_name, tools=tools, tool_choice=tool_choice
        )
        assert chat_completion.choices[0].message.tool_calls is not None
        assert len(chat_completion.choices[0].message.tool_calls) > 0
        assert chat_completion.choices[0].message.tool_calls[0].id in [
            "functions.get_current_weather:0",
            "functions.get_forecast:1",
        ]
    else:
        # Streaming test
        output_stream = await k2_client.chat.completions.create(
            messages=messages,
            model=model_name,
            tools=tools,
            tool_choice=tool_choice,
            stream=True,
        )

        output = []
        async for chunk in output_stream:
            if chunk.choices and chunk.choices[0].delta.tool_calls:
                output.extend(chunk.choices[0].delta.tool_calls)
        for o in output:
            assert o.id is None or o.id in [
                "functions.get_current_weather:0",
                "functions.get_forecast:1",
            ]