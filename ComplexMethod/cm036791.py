async def test_chat_completion_with_tool_use(server):
    """Test chat completion with tool use (get_weather function)."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "The unit of temperature",
                        },
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    async with server.get_async_client() as client:
        # Test with return_token_ids enabled
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What's the weather like in Paris?"},
            ],
            tools=tools,
            tool_choice="auto",
            max_tokens=100,
            temperature=0,
            logprobs=True,
            extra_body={"return_token_ids": True},
        )

        # Verify token_ids field is present in choices
        assert response.choices[0].token_ids is not None
        assert isinstance(response.choices[0].token_ids, list)

        # Verify prompt_token_ids field is present
        assert response.prompt_token_ids is not None
        assert isinstance(response.prompt_token_ids, list)

        # Verify the prompt texts and response texts
        tokenizer = get_tokenizer(tokenizer_name=MODEL_NAME)
        prompt_text = tokenizer.decode(response.prompt_token_ids)
        assert prompt_text.startswith(
            "<|im_start|>system\nYou are a helpful assistant."
        )
        assert prompt_text.endswith(
            "What's the weather like in Paris?<|im_end|>\n<|im_start|>assistant\n"
        )

        response_text = tokenizer.decode(response.choices[0].token_ids)
        assert response_text.startswith('<tool_call>\n{"name": "get_weather"')
        assert response_text.endswith("</tool_call><|im_end|>")

        # If tool call was made, verify the response structure
        if response.choices[0].message.tool_calls:
            assert len(response.choices[0].message.tool_calls) > 0
            tool_call = response.choices[0].message.tool_calls[0]
            assert tool_call.function.name == "get_weather"

        # Test without return_token_ids
        response_without = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What's the weather like in Paris?"},
            ],
            tools=tools,
            tool_choice="auto",
            max_tokens=100,
            temperature=0,
            logprobs=True,
            extra_body={"return_token_ids": False},
        )

        assert response_without.choices[0].token_ids is None
        assert response_without.prompt_token_ids is None