async def test_api_only_multinode_dp_completion_streaming(
    api_only_client: openai.AsyncOpenAI,
    api_only_servers: list[tuple[RemoteOpenAIServer, list[str]]],
    model_name: str,
) -> None:
    """Test API-only server streaming with all engines on separate
    headless server."""
    prompt = "What is an LLM?"

    async def make_streaming_request():
        # Perform a non-streaming request to get the expected full output
        single_completion = await api_only_client.completions.create(
            model=model_name,
            prompt=prompt,
            max_tokens=5,
            temperature=0.0,
        )
        single_output = single_completion.choices[0].text

        # Perform the streaming request
        stream = await api_only_client.completions.create(
            model=model_name, prompt=prompt, max_tokens=5, temperature=0.0, stream=True
        )
        chunks: list[str] = []
        finish_reason_count = 0
        last_chunk = None
        async for chunk in stream:
            chunks.append(chunk.choices[0].text)
            if chunk.choices[0].finish_reason is not None:
                finish_reason_count += 1
            last_chunk = chunk  # Keep track of the last chunk

        # finish reason should only return in the last block for OpenAI API
        assert finish_reason_count == 1, "Finish reason should appear exactly once."
        assert last_chunk is not None, "Stream should have yielded at least one chunk."
        assert last_chunk.choices[0].finish_reason == "length", (
            "Finish reason should be 'length'."
        )
        # Check that the combined text matches the non-streamed version.
        assert "".join(chunks) == single_output, (
            "Streamed output should match non-streamed output."
        )
        return True  # Indicate success for this request

    # Test single streaming request
    result = await make_streaming_request()
    assert result is not None
    print("API-only server handled single streaming request successfully")

    await asyncio.sleep(0.5)

    # Send multiple streaming requests - should be distributed across engines
    num_requests = 200
    all_tasks = []
    for _ in range(num_requests):
        all_tasks.append(asyncio.create_task(make_streaming_request()))
        await asyncio.sleep(0.01)

    results = await asyncio.gather(*all_tasks)
    assert len(results) == num_requests
    assert all(results), "Not all streaming requests completed successfully."

    await asyncio.sleep(0.5)

    # Second burst of streaming requests
    all_tasks = []
    for _ in range(num_requests):
        all_tasks.append(asyncio.create_task(make_streaming_request()))
        await asyncio.sleep(0.01)

    results = await asyncio.gather(*all_tasks)
    assert len(results) == num_requests
    assert all(results), "Not all streaming requests completed successfully."

    _, api_server_args = api_only_servers[0]
    api_server_count = (
        api_server_args.count("--api-server-count")
        and api_server_args[api_server_args.index("--api-server-count") + 1]
        or 1
    )
    print(
        f"Successfully completed API-only streaming test with {DP_SIZE} "
        f"engines on headless server (API server count: {api_server_count})"
    )

    # Check request balancing via Prometheus metrics
    api_server = api_only_servers[0][0]
    check_request_balancing(api_server, DP_SIZE)