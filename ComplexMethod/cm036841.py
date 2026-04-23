async def test_gpt_oss_chat_tool_call_streaming(
        self, gptoss_client: OpenAI, with_tool_parser: bool
    ):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                            },
                        },
                        "required": ["city", "state", "unit"],
                    },
                },
            }
        ]

        messages = [
            {"role": "user", "content": "What is the weather in Dallas, TX?"},
        ]

        stream = await gptoss_client.chat.completions.create(
            model=GPT_OSS_MODEL_NAME,
            messages=messages,
            tools=tools if with_tool_parser else None,
            stream=True,
        )

        name = None
        args_buf = ""
        content_buf = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.tool_calls:
                tc = delta.tool_calls[0]
                if tc.function and tc.function.name:
                    name = tc.function.name
                if tc.function and tc.function.arguments:
                    args_buf += tc.function.arguments
            if getattr(delta, "content", None):
                content_buf += delta.content
        if with_tool_parser:
            assert name is not None
            assert len(args_buf) > 0
        else:
            assert name is None
            assert len(args_buf) == 0
            assert len(content_buf) > 0