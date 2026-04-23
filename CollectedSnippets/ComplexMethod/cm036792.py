async def test_comparison_with_prompt_logprobs_and_logprobs(server):
    """
    Test that token_ids align with prompt_logprobs and
    logprobs when return_tokens_as_token_ids is enabled.
    """
    async with server.get_async_client() as client:
        # Test with both return_token_ids and return_tokens_as_token_ids enabled
        completion = await client.completions.create(
            model=MODEL_NAME,
            prompt="Hello, world! How are you today?",
            max_tokens=20,
            temperature=0,
            echo=True,
            logprobs=1,
            extra_body={
                "return_token_ids": True,
                "return_tokens_as_token_ids": True,
                "prompt_logprobs": 1,
            },
        )

        # Verify all fields are present
        assert completion.choices[0].token_ids is not None
        assert completion.choices[0].prompt_token_ids is not None
        assert completion.choices[0].prompt_logprobs is not None
        assert completion.choices[0].logprobs is not None

        # Extract token IDs from logprobs
        # (when return_tokens_as_token_ids is True)
        logprobs_token_ids = []
        for token_str in completion.choices[0].logprobs.tokens:
            # Token format is "token_id:12345" when
            # return_tokens_as_token_ids is True
            if token_str.startswith("token_id:"):
                token_id = int(token_str.removeprefix("token_id:"))
                logprobs_token_ids.append(token_id)

        # When echo=True, the logprobs include both prompt and response tokens
        # The token_ids field should match the suffix of response portion
        # The prompt_token_ids should match the prompt portion
        assert len(completion.choices[0].token_ids) < len(logprobs_token_ids)
        response_token_ids_length = len(completion.choices[0].token_ids)
        assert (
            logprobs_token_ids[-response_token_ids_length:]
            == completion.choices[0].token_ids
        )

        # Verify tokenizer consistency
        tokenizer = get_tokenizer(tokenizer_name=MODEL_NAME)

        # Decode prompt tokens
        if completion.choices[0].prompt_token_ids:
            prompt_text = tokenizer.decode(completion.choices[0].prompt_token_ids)
            # The decoded prompt should match or close to original prompt
            assert "Hello, world" in prompt_text

        # Decode response tokens
        if completion.choices[0].token_ids:
            response_text = tokenizer.decode(completion.choices[0].token_ids)
            assert completion.choices[0].text.endswith(response_text)

        # Test streaming mode
        stream = await client.completions.create(
            model=MODEL_NAME,
            prompt="Tell me a short fact about Python:",
            max_tokens=30,
            temperature=0,
            stream=True,
            echo=False,
            logprobs=1,
            extra_body={"return_token_ids": True, "return_tokens_as_token_ids": True},
        )

        # Collect streamed tokens
        streamed_prompt_token_ids = []
        streamed_token_ids = []
        streamed_logprob_token_ids = []
        first_chunk = True
        async for chunk in stream:
            for token_str in chunk.choices[0].logprobs.tokens:
                # Token format is "token_id:12345" when
                # return_tokens_as_token_ids is True
                if token_str.startswith("token_id:"):
                    token_id = int(token_str.removeprefix("token_id:"))
                    streamed_logprob_token_ids.append(token_id)
            if first_chunk:
                streamed_prompt_token_ids = chunk.choices[0].prompt_token_ids
                first_chunk = False
            streamed_token_ids += chunk.choices[0].token_ids

        # Verify we collected some tokens and first chunk had prompt_token_ids
        assert len(streamed_prompt_token_ids) > 0
        assert streamed_token_ids == streamed_logprob_token_ids