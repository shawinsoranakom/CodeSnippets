def test_kv_cache_events(
    multiprocessing_mode: bool,
    publisher_config,
    model_name: str,
    num_groups: int,
):
    block_size = 16
    num_blocks = 2

    engine_args = EngineArgs(
        model=model_name,
        enforce_eager=True,
        enable_prefix_caching=True,
        block_size=block_size,
    )
    engine_args.kv_events_config = publisher_config

    vllm_config = engine_args.create_engine_config(UsageContext.UNKNOWN_CONTEXT)

    executor_class = Executor.get_class(vllm_config)
    with set_default_torch_num_threads(1):
        client = EngineCoreClient.make_client(
            multiprocess_mode=multiprocessing_mode,
            asyncio_mode=False,
            vllm_config=vllm_config,
            executor_class=executor_class,
            log_stats=False,
        )
    endpoint = publisher_config.endpoint.replace("*", "127.0.0.1")
    subscriber = MockSubscriber(
        endpoint, topic=publisher_config.topic, decode_type=KVEventBatch
    )

    try:
        custom_tokens = list(range(num_blocks * block_size))
        sampling_params = SamplingParams(max_tokens=1)
        request = make_request(sampling_params, custom_tokens)
        client.add_request(request)

        outputs: dict[str, list] = {request.request_id: []}
        loop_until_done(client, outputs)

        result = subscriber.receive_one(timeout=1000)
        assert result is not None, "No message received"

        seq, received = result
        assert seq == 0, "Sequence number mismatch"
        assert len(received.events) == num_groups, (
            f"Expected {num_groups} BlockStored event(s), got {len(received.events)}"
        )

        for index, event in enumerate(received.events):
            assert isinstance(event, BlockStored), "We should have a BlockStored event"
            assert len(event.block_hashes) == num_blocks, (
                "We should have a BlockStored event with 2 block_hashes"
            )
            assert event.block_size == block_size, (
                "Block size should be the same as the block size"
            )
            assert event.parent_block_hash is None, "Parent block hash should be None"
            assert event.lora_id is None, "Lora id should be None"
            assert event.lora_name is None, "Lora name should be None"
            assert len(event.token_ids) == num_blocks * block_size, (
                "Token ids should be the same as the custom tokens"
            )
            assert event.token_ids == custom_tokens, (
                "Token ids should be the same as the custom tokens"
            )
            assert event.group_idx == index
    finally:
        client.shutdown()
        subscriber.close()