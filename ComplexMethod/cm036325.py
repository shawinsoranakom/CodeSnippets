def test_encoder_instance_zero_kv_cache(
    ec_role: str,
    gpu_memory_utilization: float,
    enable_prefix_caching: bool,
    use_kv_connector: bool,
):
    """EPD (Encoder-Prefill-Decode) Encoder-cache-specific tests

    This test verifies encoder-only instance initializes with 0 KV cache blocks.
    Under EPD disagg mode, Encoder instances (EC producer role) only execute
    vision encoder, so they don't need KV cache for text generation.
    """
    # Form vllm config
    model_config = ModelConfig(
        model="llava-hf/llava-1.5-7b-hf",  # Multimodal model
        enforce_eager=True,
        trust_remote_code=True,
        dtype="float16",
        seed=42,
    )
    scheduler_config = SchedulerConfig(
        max_num_seqs=10,
        max_num_batched_tokens=512,
        max_model_len=512,
        disable_hybrid_kv_cache_manager=True,
        is_encoder_decoder=model_config.is_encoder_decoder,
    )
    cache_config = CacheConfig(
        block_size=16,
        gpu_memory_utilization=gpu_memory_utilization,
        cache_dtype="auto",
        enable_prefix_caching=enable_prefix_caching,
    )
    kv_transfer_config = (
        KVTransferConfig(
            kv_connector="ExampleConnector",
            kv_role="kv_both",
            kv_connector_extra_config={"shared_storage_path": "local_storage"},
        )
        if use_kv_connector
        else None
    )
    ec_transfer_config = ECTransferConfig(
        ec_connector="ECExampleConnector",
        ec_role=ec_role,
        ec_connector_extra_config={"shared_storage_path": "/tmp/ec_test_encoder"},
    )

    vllm_config = VllmConfig(
        model_config=model_config,
        cache_config=cache_config,
        scheduler_config=scheduler_config,
        kv_transfer_config=kv_transfer_config,
        ec_transfer_config=ec_transfer_config,
    )

    executor_class = Executor.get_class(vllm_config)
    print(f"executor_class: {executor_class}")

    with set_default_torch_num_threads(1):
        engine_core = EngineCore(
            vllm_config=vllm_config, executor_class=executor_class, log_stats=True
        )

    # Check encoder cache manager exists
    assert engine_core.scheduler.encoder_cache_manager is not None, (
        "encoder_cache_manager should exist"
    )

    if ec_role == "ec_producer":
        # Check 1: num_blocks should be 0
        # NOTE: num_blocks=1 as BlockPool always needs a null_block.
        kv_cache_config = engine_core.scheduler.kv_cache_manager.kv_cache_config
        print(f"kv_cache_config: {kv_cache_config}")
        assert kv_cache_config.num_blocks == 1, (
            f"ec_producer should only have 1 KV blocks, "
            f"got {kv_cache_config.num_blocks}"
        )

        # Check 2: kv_cache_groups should be empty
        assert len(kv_cache_config.kv_cache_groups) == 0, (
            f"ec_producer should have 0 KV cache groups, "
            f"got {len(kv_cache_config.kv_cache_groups)}"
        )

        # Check 3: kv_cache_tensors should be empty
        assert len(kv_cache_config.kv_cache_tensors) == 0, (
            f"Encoder instance should have 0 KV cache tensors, "
            f"got {len(kv_cache_config.kv_cache_tensors)}"
        )

        # Check 4: Verify EC connector is initialized and is producer
        assert engine_core.scheduler.ec_connector is not None, (
            "Encoder instance should have EC connector"
        )
        assert engine_core.scheduler.ec_connector.is_producer, (
            "Encoder instance EC connector should be producer"
        )

        # Check 5: Verify chunked prefill is disabled
        assert not vllm_config.scheduler_config.enable_chunked_prefill, (
            "Encoder instance should disable chunked prefill (no KV cache)"
        )

    elif ec_role == "ec_consumer":
        # Check 1: num_blocks should be > 1
        kv_cache_config = engine_core.scheduler.kv_cache_manager.kv_cache_config
        print(f"kv_cache_config: {kv_cache_config}")
        assert kv_cache_config.num_blocks > 1, (
            f"ec_consumer should have >1 KV blocks, got {kv_cache_config.num_blocks}"
        )

        # Check 2: kv_cache_groups should NOT be empty
        assert len(kv_cache_config.kv_cache_groups) > 0, (
            f"ec_consumer should have KV cache groups, "
            f"got {len(kv_cache_config.kv_cache_groups)}"
        )

        # Check 3: Verify EC connector is consumer
        assert engine_core.scheduler.ec_connector is not None, (
            "Consumer instance should have EC connector"
        )
        assert not engine_core.scheduler.ec_connector.is_producer, (
            "Consumer instance EC connector should be consumer"
        )