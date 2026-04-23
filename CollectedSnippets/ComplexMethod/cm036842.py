async def test_gpt_oss_tool_message_array_content(
        self, gptoss_client: OpenAI, with_tool_parser: bool
    ):
        """Test that tool messages support both string and array content formats."""
        if not with_tool_parser:
            pytest.skip("skip non-tool for array content tests")

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                        },
                        "required": ["city", "state"],
                    },
                },
            }
        ]

        # Test 1: Tool message with string content
        messages_string = [
            {"role": "user", "content": "What's the weather in Paris?"},
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city": "Paris", "state": "TX"}',
                        },
                    }
                ],
            },
            {"role": "tool", "content": "The weather in Paris, TX is sunny, 22°C"},
        ]

        response_string = await gptoss_client.chat.completions.create(
            model=GPT_OSS_MODEL_NAME,
            messages=messages_string,
            tools=tools,
            temperature=0.0,
        )

        assert response_string is not None
        assert response_string.choices[0].message is not None

        # Test 2: Tool message with array content
        messages_array = [
            {"role": "user", "content": "What's the weather in Dallas?"},
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_456",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city": "Dallas", "state": "TX"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "content": [
                    {"type": "text", "text": "f2e897a7-2705-4337-8193-2a8f57b81618"}
                ],
            },
        ]

        response_array = await gptoss_client.chat.completions.create(
            model=GPT_OSS_MODEL_NAME,
            messages=messages_array,
            tools=tools,
            temperature=0.0,
        )

        assert response_array is not None
        assert response_array.choices[0].message is not None

        # Test 3: Tool message with multiple array content items
        messages_multi_array = [
            {"role": "user", "content": "Search for information"},
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_789",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city": "Austin", "state": "TX"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "content": [
                    {"type": "text", "text": "Weather data: "},
                    {"type": "text", "text": "Austin, TX - Partly cloudy, 25°C"},
                    {"type": "text", "text": " with 60% humidity"},
                ],
            },
        ]

        response_multi_array = await gptoss_client.chat.completions.create(
            model=GPT_OSS_MODEL_NAME,
            messages=messages_multi_array,
            tools=tools,
            temperature=0.0,
        )

        assert response_multi_array is not None
        assert response_multi_array.choices[0].message is not None