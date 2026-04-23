async def test_completion_stream_options(client: openai.AsyncOpenAI, model_name: str):
    prompt = "What is the capital of France?"

    # Test stream=True, stream_options=
    #     {"include_usage": False, "continuous_usage_stats": False}
    stream = await client.completions.create(
        model=model_name,
        prompt=prompt,
        max_tokens=5,
        temperature=0.0,
        stream=True,
        stream_options={
            "include_usage": False,
            "continuous_usage_stats": False,
        },
    )

    async for chunk in stream:
        assert chunk.usage is None

    # Test stream=True, stream_options=
    #     {"include_usage": False, "continuous_usage_stats": True}
    stream = await client.completions.create(
        model=model_name,
        prompt=prompt,
        max_tokens=5,
        temperature=0.0,
        stream=True,
        stream_options={
            "include_usage": False,
            "continuous_usage_stats": True,
        },
    )
    async for chunk in stream:
        assert chunk.usage is None

    # Test stream=True, stream_options=
    #     {"include_usage": True, "continuous_usage_stats": False}
    stream = await client.completions.create(
        model=model_name,
        prompt=prompt,
        max_tokens=5,
        temperature=0.0,
        stream=True,
        stream_options={
            "include_usage": True,
            "continuous_usage_stats": False,
        },
    )
    async for chunk in stream:
        if chunk.choices[0].finish_reason is None:
            assert chunk.usage is None
        else:
            assert chunk.usage is None
            final_chunk = await anext(stream)
            assert final_chunk.usage is not None
            assert final_chunk.usage.prompt_tokens > 0
            assert final_chunk.usage.completion_tokens > 0
            assert final_chunk.usage.total_tokens == (
                final_chunk.usage.prompt_tokens + final_chunk.usage.completion_tokens
            )
            assert final_chunk.choices == []

    # Test stream=True, stream_options=
    #     {"include_usage": True, "continuous_usage_stats": True}
    stream = await client.completions.create(
        model=model_name,
        prompt=prompt,
        max_tokens=5,
        temperature=0.0,
        stream=True,
        stream_options={
            "include_usage": True,
            "continuous_usage_stats": True,
        },
    )
    async for chunk in stream:
        assert chunk.usage is not None
        assert chunk.usage.prompt_tokens > 0
        assert chunk.usage.completion_tokens > 0
        assert chunk.usage.total_tokens == (
            chunk.usage.prompt_tokens + chunk.usage.completion_tokens
        )
        if chunk.choices[0].finish_reason is not None:
            final_chunk = await anext(stream)
            assert final_chunk.usage is not None
            assert final_chunk.usage.prompt_tokens > 0
            assert final_chunk.usage.completion_tokens > 0
            assert final_chunk.usage.total_tokens == (
                final_chunk.usage.prompt_tokens + final_chunk.usage.completion_tokens
            )
            assert final_chunk.choices == []

    # Test stream=True, stream_options={}
    stream = await client.completions.create(
        model=model_name,
        prompt=prompt,
        max_tokens=5,
        temperature=0.0,
        stream=True,
        stream_options={},
    )
    async for chunk in stream:
        assert chunk.usage is None

    # Test stream=False, stream_options=
    #     {"include_usage": None}
    with pytest.raises(BadRequestError):
        await client.completions.create(
            model=model_name,
            prompt=prompt,
            max_tokens=5,
            temperature=0.0,
            stream=False,
            stream_options={"include_usage": None},
        )

    # Test stream=False, stream_options=
    #    {"include_usage": True}
    with pytest.raises(BadRequestError):
        await client.completions.create(
            model=model_name,
            prompt=prompt,
            max_tokens=5,
            temperature=0.0,
            stream=False,
            stream_options={"include_usage": True},
        )

    # Test stream=False, stream_options=
    #     {"continuous_usage_stats": None}
    with pytest.raises(BadRequestError):
        await client.completions.create(
            model=model_name,
            prompt=prompt,
            max_tokens=5,
            temperature=0.0,
            stream=False,
            stream_options={"continuous_usage_stats": None},
        )

    # Test stream=False, stream_options=
    #    {"continuous_usage_stats": True}
    with pytest.raises(BadRequestError):
        await client.completions.create(
            model=model_name,
            prompt=prompt,
            max_tokens=5,
            temperature=0.0,
            stream=False,
            stream_options={"continuous_usage_stats": True},
        )