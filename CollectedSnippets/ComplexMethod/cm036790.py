async def test_basic_completion_with_emoji(server, return_token_ids: bool | None):
    """Test basic completion with emoji to verify token_ids field."""
    extra_body = None
    if return_token_ids is not None:
        extra_body = {"return_token_ids": return_token_ids}
    async with server.get_async_client() as client:
        # Test with return_token_ids enabled
        completion = await client.completions.create(
            model=MODEL_NAME,
            prompt="Complete this sentence with emojis: I love coding 🚀",
            max_tokens=10,
            temperature=0,
            logprobs=1,
            extra_body=extra_body,
        )

        # Check the raw response to see the structure
        completion_dict = completion.model_dump()

        # Verify prompt_token_ids field is present in the completion response
        assert "prompt_token_ids" in completion_dict["choices"][0]
        if not return_token_ids:
            # If return_token_ids is False, token_ids should not be present
            assert completion_dict["choices"][0].get("token_ids") is None
            assert completion_dict["choices"][0].get("prompt_token_ids") is None
            # Skip further checks
            return
        assert isinstance(completion.choices[0].prompt_token_ids, list)

        # Check against the expected prompt token IDs
        tokenizer = get_tokenizer(tokenizer_name=MODEL_NAME)
        encoded_tokens = tokenizer.encode(
            "Complete this sentence with emojis: I love coding 🚀"
        )
        # Check that encoded_tokens is a subsequence of prompt_token_ids
        assert any(
            completion.choices[0].prompt_token_ids[i : i + len(encoded_tokens)]
            == encoded_tokens
            for i in range(
                len(completion.choices[0].prompt_token_ids) - len(encoded_tokens) + 1
            )
        )

        # Verify token_ids field is present in the choice
        assert completion.choices[0].token_ids is not None
        assert isinstance(completion.choices[0].token_ids, list)
        assert len(completion.choices[0].token_ids) > 0

        # Verify decoding works correctly
        decoded_text = tokenizer.decode(completion.choices[0].token_ids)
        # The decoded text should contain a <|im_end|> at the end
        assert decoded_text.startswith(completion.choices[0].text)

        # Test without return_token_ids (should be None)
        completion_without = await client.completions.create(
            model=MODEL_NAME,
            prompt="Complete this sentence with emojis: I love coding 🚀",
            max_tokens=10,
            temperature=0,
            logprobs=1,
            extra_body={"return_token_ids": False},
        )

        completion_without_dict = completion_without.model_dump()
        assert completion_without_dict["choices"][0].get("token_ids") is None
        assert completion_without_dict.get("prompt_token_ids") is None