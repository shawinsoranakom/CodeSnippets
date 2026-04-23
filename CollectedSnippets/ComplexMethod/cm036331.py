async def test_kv_cache_events_dp(
    multiprocessing_mode: bool,
    publisher_config,
):
    block_size = 16
    num_blocks = 2
    dp_size = 2
    tp_size = 2

    engine_args = EngineArgs(
        model=MODEL_NAME,
        enforce_eager=True,
        enable_prefix_caching=True,
        data_parallel_size=dp_size,
        tensor_parallel_size=tp_size,
        block_size=block_size,
    )
    engine_args.kv_events_config = publisher_config

    vllm_config = engine_args.create_engine_config(UsageContext.UNKNOWN_CONTEXT)

    executor_class = Executor.get_class(vllm_config)
    with set_default_torch_num_threads(1):
        client = EngineCoreClient.make_client(
            multiprocess_mode=multiprocessing_mode,
            asyncio_mode=True,
            vllm_config=vllm_config,
            executor_class=executor_class,
            log_stats=False,
        )
    await asyncio.sleep(1)

    # Build endpoints for all DP ranks
    base_endpoint = publisher_config.endpoint.replace("*", "127.0.0.1")
    endpoints = []
    for i in range(dp_size):
        offset_endpoint = ZmqEventPublisher.offset_endpoint_port(base_endpoint, i)
        endpoints.append(offset_endpoint)

    subscriber = MockSubscriber(
        endpoints, topic=publisher_config.topic, decode_type=KVEventBatch
    )

    try:
        custom_tokens = list(range(num_blocks * block_size))
        sampling_params = SamplingParams(max_tokens=1)
        all_request_ids = []

        # Create and add 25 requests
        # NOTE: attempts to force routing to both dp groups but can be flaky
        for i in range(25):
            await asyncio.sleep(0.01)
            request = make_request(sampling_params, custom_tokens)
            await client.add_request_async(request)
            all_request_ids.append(request.request_id)

        await asyncio.sleep(0.1)

        # Initialize outputs dict for all requests
        outputs: dict[str, list] = {req_id: [] for req_id in all_request_ids}

        print("processing requests...")
        await asyncio.wait_for(
            loop_until_fully_done_async(client, outputs), timeout=20.0
        )

        # Receive from subscriber until no more messages
        print("collecting results...")
        results = []
        while True:
            result = subscriber.receive_one(timeout=1)
            print(result)
            if result is None:
                break
            results.append(result)

        # Collect all events and data_parallel_ranks from all results
        all_dp_ranks = [received.data_parallel_rank for (_, received) in results]
        unique_dps = set(all_dp_ranks)
        assert len(unique_dps) == 2, (
            f"Expected 2 unique data_parallel_ranks, got {len(unique_dps)}"
        )

    finally:
        client.shutdown()
        subscriber.close()