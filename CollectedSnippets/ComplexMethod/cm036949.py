async def test_abort_metrics_reset(
    server: RemoteOpenAIServer,
    client: openai.AsyncClient,
    model_key: str,
):
    model_name = MODELS[model_key]
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    prompt_ids = tokenizer.encode(_PROMPT)

    running_requests, waiting_requests, kv_cache_usage = _get_running_metrics_from_api(
        server,
    )

    # Expect no running requests or kvcache usage
    assert running_requests == 0
    assert waiting_requests == 0
    assert kv_cache_usage == 0.0

    # Start some long-running requests that we can abort
    tasks = []
    for _ in range(3):
        task = asyncio.create_task(
            client.completions.create(
                model=model_name,
                prompt=prompt_ids,
                max_tokens=500,  # Long generation to give time to abort
                temperature=0.0,
            )
        )
        tasks.append(task)

    # Poll until we see running requests rather than using a fixed sleep,
    # since generation speed varies across hardware.
    try:
        await _poll_until(
            lambda: _get_running_metrics_from_api(server)[0] > 0,
            timeout=10.0,
            interval=0.1,
            description="running_requests > 0",
        )
    except TimeoutError:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        pytest.fail("Requests never appeared as running in metrics")

    # Check that we have running requests
    running_requests, waiting_requests, kv_cache_usage = _get_running_metrics_from_api(
        server,
    )

    # Expect running requests and kvcache usage
    assert running_requests > 0
    assert kv_cache_usage > 0

    # Cancel all tasks to abort the requests
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    # Poll until metrics reset rather than using a fixed sleep
    await _poll_until(
        lambda: _get_running_metrics_from_api(server) == (0, 0, 0),
        timeout=10.0,
        interval=0.2,
        description="gauge metrics back to zero",
    )

    # Verify running and waiting requests counts and KV cache usage are zero
    running_requests_after, waiting_requests_after, kv_cache_usage_after = (
        _get_running_metrics_from_api(server)
    )

    assert running_requests_after == 0, (
        f"Expected 0 running requests after abort, got {running_requests_after}"
    )
    assert waiting_requests_after == 0, (
        f"Expected 0 waiting requests after abort, got {waiting_requests_after}"
    )
    assert kv_cache_usage_after == 0, (
        f"Expected 0% KV cache usage after abort, got {kv_cache_usage_after}"
    )