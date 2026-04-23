async def test_completion_stream_options_and_logprobs_with_long_prompts(
    client: openai.AsyncOpenAI,
):
    # Test stream with long prompt
    prompt = "What is the capital of France?" * 400

    stream = await client.completions.create(
        model=MODEL_NAME,
        prompt=prompt,
        max_tokens=5,
        temperature=0.0,
        stream=True,
        stream_options={
            "include_usage": True,
            "continuous_usage_stats": True,
        },
        logprobs=5,
    )

    tokens_received = 0
    finished = False
    async for chunk in stream:
        assert chunk.usage.prompt_tokens >= 0
        assert chunk.usage.completion_tokens >= 0
        assert chunk.usage.total_tokens == (
            chunk.usage.prompt_tokens + chunk.usage.completion_tokens
        )
        if not finished:
            assert chunk.choices[0].text
            # Count actual tokens from logprobs since multiple tokens
            # can be batched into a single chunk
            assert chunk.choices[0].logprobs and chunk.choices[0].logprobs.tokens
            tokens_received += len(chunk.choices[0].logprobs.tokens)

            if chunk.choices[0].finish_reason is not None:
                finished = True

        if finished:
            assert chunk.usage.completion_tokens == tokens_received