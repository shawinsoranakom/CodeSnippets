async def test_hybrid_lb_completion(
    clients: list[openai.AsyncOpenAI],
    servers: list[tuple[RemoteOpenAIServer, list[str]]],
    model_name: str,
) -> None:
    async def make_request(client: openai.AsyncOpenAI):
        completion = await client.completions.create(
            model=model_name, prompt="Hello, my name is", max_tokens=5, temperature=1.0
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

    # Test single request to each node
    for i, client in enumerate(clients):
        result = await make_request(client)
        assert result is not None
        print(f"Hybrid LB node {i} handled single completion request successfully")

    await asyncio.sleep(0.5)

    # Send requests to all nodes - each should balance within its local DP ranks
    num_requests = 200  # Total 200 requests across 2 nodes
    all_tasks = []
    for i in range(num_requests):
        client = clients[i % len(clients)]
        all_tasks.append(asyncio.create_task(make_request(client)))
        await asyncio.sleep(0.01)

    results = await asyncio.gather(*all_tasks)
    assert len(results) == num_requests
    assert all(completion is not None for completion in results)

    await asyncio.sleep(0.5)

    # Second burst of requests
    all_tasks = []
    for i in range(num_requests):
        client = clients[i % len(clients)]
        all_tasks.append(asyncio.create_task(make_request(client)))
        await asyncio.sleep(0.01)

    results = await asyncio.gather(*all_tasks)
    assert len(results) == num_requests
    assert all(completion is not None for completion in results)

    _, server_args = servers[0]
    api_server_count = (
        server_args.count("--api-server-count")
        and server_args[server_args.index("--api-server-count") + 1]
        or 1
    )
    print(
        f"Successfully completed hybrid LB test with {len(clients)} nodes "
        f"({DP_SIZE_LOCAL} DP ranks each, API server count: {api_server_count})"
    )

    # Check request balancing within each node
    for i, (server, _) in enumerate(servers):
        print(f"Checking request balancing for node {i}")
        check_request_balancing(server, DP_SIZE_LOCAL)