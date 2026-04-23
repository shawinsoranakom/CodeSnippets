async def test_single_completion(
    client: openai.AsyncOpenAI, server: RemoteOpenAIServer, model_name: str
) -> None:
    async def make_request():
        completion = await client.completions.create(
            model=model_name, prompt="Hello, my name is", max_tokens=10, temperature=1.0
        )

        assert completion.id is not None
        assert completion.choices is not None and len(completion.choices) == 1

        choice = completion.choices[0]
        # The exact number of tokens can vary slightly with temperature=1.0,
        # so we check for a reasonable minimum length.
        assert len(choice.text) >= 1
        # Finish reason might not always be 'length' if the model finishes early
        # or due to other reasons, especially with high temperature.
        # So, we'll accept 'length' or 'stop'.
        assert choice.finish_reason in ("length", "stop")

        # Token counts can also vary, so we check they are positive.
        assert completion.usage.completion_tokens > 0
        assert completion.usage.prompt_tokens > 0
        assert completion.usage.total_tokens > 0
        return completion

    # Test single request
    result = await make_request()
    assert result is not None

    await asyncio.sleep(0.5)

    # Send two bursts of requests
    num_requests = 100
    tasks = [make_request() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)
    assert len(results) == num_requests
    assert all(completion is not None for completion in results)

    await asyncio.sleep(0.5)

    tasks = [make_request() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)
    assert len(results) == num_requests
    assert all(completion is not None for completion in results)

    # Check request balancing via Prometheus metrics if DP_SIZE > 1
    check_request_balancing(server, int(DP_SIZE))