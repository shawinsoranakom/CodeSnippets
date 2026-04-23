async def test_chat_completion_with_emoji_and_token_ids(server):
    """Test chat completion with emojis to verify token_ids handling."""
    chat_messages = [
        {"role": "system", "content": "You like to use emojis in your responses."},
        {"role": "user", "content": "Repeat after me: I love cats 🐱"},
    ]
    async with server.get_async_client() as client:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=chat_messages,
            max_tokens=50,
            temperature=0,
            logprobs=True,
            extra_body={"return_token_ids": True},
        )

        # Verify token_ids are present
        response_dict = response.model_dump()
        assert response.choices[0].token_ids is not None
        assert "prompt_token_ids" in response_dict

        # Verify the response contains the expected fields
        assert response.choices[0].message.content is not None

        # Decode token_ids and verify consistency
        tokenizer = get_tokenizer(tokenizer_name=MODEL_NAME)

        decoded_prompt = tokenizer.decode(response.prompt_token_ids)
        assert decoded_prompt.startswith(
            "<|im_start|>system\nYou like to use emojis in your responses."
        )
        assert decoded_prompt.endswith(
            "I love cats 🐱<|im_end|>\n<|im_start|>assistant\n"
        )

        decoded_response = tokenizer.decode(response.choices[0].token_ids)
        # The content should match the response text
        # except the ending <|im_end|>
        assert decoded_response == response.choices[0].message.content + "<|im_end|>"

        # Test with streaming
        stream = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=chat_messages,
            max_tokens=50,
            temperature=0,
            stream=True,
            extra_body={"return_token_ids": True},
        )

        collected_content = ""
        collected_token_ids = []
        first_chunk = True

        async for chunk in stream:
            if first_chunk:
                assert chunk.prompt_token_ids is not None
                assert isinstance(chunk.prompt_token_ids, list)
                # Check the prompt_token_ids match the initial prompt
                decoded_prompt_stream = tokenizer.decode(chunk.prompt_token_ids)
                assert decoded_prompt_stream == decoded_prompt
                first_chunk = False
            else:
                chunk_dump = chunk.model_dump()
                assert "prompt_token_ids" not in chunk_dump, (
                    "Subsequent chunks should not have prompt_token_ids"
                )

            if chunk.choices:
                if chunk.choices[0].delta.content:
                    collected_content += chunk.choices[0].delta.content
                # token_ids may not present in all chunks
                choice_dump = chunk.choices[0].model_dump()
                if "token_ids" in choice_dump:
                    collected_token_ids.extend(chunk.choices[0].token_ids)

        # Verify we got response and token_ids
        assert len(collected_content) > 0
        assert len(collected_token_ids) > 0

        # Verify token_ids decode properly
        decoded_response = tokenizer.decode(collected_token_ids)
        assert decoded_response == collected_content + "<|im_end|>"