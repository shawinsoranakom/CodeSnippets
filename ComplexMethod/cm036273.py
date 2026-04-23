def create_scheduler(
    model: str = "facebook/opt-125m",
    max_num_seqs: int = 16,
    max_num_batched_tokens: int = 8192,
    enable_chunked_prefill: bool = True,
    enable_prefix_caching: bool = False,
    long_prefill_token_threshold: int = 0,
    disable_chunked_mm_input: bool = False,
    use_kv_connector: None | bool | str | MockKVConfig = None,
    num_blocks: int = 10000,
    block_size: int = 16,
    max_model_len: int | None = None,
    num_speculative_tokens: int | None = None,
    skip_tokenizer_init: bool = False,
    async_scheduling: bool = False,
    pipeline_parallel_size: int = 1,
    use_ec_connector: bool = False,
    ec_role: str | None = None,
) -> Scheduler | AsyncScheduler:
    """Create scheduler under test.

    Args:
      model: model under test
      max_num_seqs: max sequences to schedule
      max_num_batch_tokens: max num tokens to batch
      enable_prefix_caching: optionally force APC config
                             (True/False) or use default
                             (False)

    Returns:
      {class}`Scheduler` instance
    """
    model_config = ModelConfig(
        model=model,
        trust_remote_code=True,
        dtype="float16",
        seed=42,
        skip_tokenizer_init=skip_tokenizer_init,
    )
    if max_model_len is None:
        max_model_len = max_num_batched_tokens
    scheduler_config = SchedulerConfig(
        max_num_seqs=max_num_seqs,
        max_num_batched_tokens=max_num_batched_tokens,
        max_model_len=max_model_len,
        long_prefill_token_threshold=long_prefill_token_threshold,
        disable_chunked_mm_input=disable_chunked_mm_input,
        enable_chunked_prefill=enable_chunked_prefill,
        async_scheduling=async_scheduling,
        is_encoder_decoder=model_config.is_encoder_decoder,
    )
    # Cache config, optionally force APC
    cache_config = CacheConfig(
        block_size=block_size,
        gpu_memory_utilization=0.9,
        cache_dtype="auto",
        enable_prefix_caching=enable_prefix_caching,
    )
    kv_transfer_config = None
    if isinstance(use_kv_connector, MockKVConfig):
        kv_transfer_config = KVTransferConfig(
            kv_connector="MockKVConnector",
            kv_role="kv_both",
            kv_connector_extra_config={
                "matched_tokens": use_kv_connector.matched_tokens,
                "is_async": use_kv_connector.is_async,
            },
        )
    elif isinstance(use_kv_connector, str):
        kv_transfer_config = KVTransferConfig(
            kv_connector=use_kv_connector,
            kv_role="kv_both",
        )
    elif use_kv_connector:
        kv_transfer_config = KVTransferConfig(
            kv_connector="ExampleConnector",
            kv_role="kv_both",
            kv_connector_extra_config={"shared_storage_path": "local_storage"},
        )

    speculative_config: SpeculativeConfig | None = None
    if num_speculative_tokens is not None:
        speculative_config = SpeculativeConfig(
            model="ngram", num_speculative_tokens=num_speculative_tokens
        )

    ec_transfer_config = (
        ECTransferConfig(
            ec_connector="ECExampleConnector",
            ec_role=ec_role,
            ec_connector_extra_config={"shared_storage_path": "/tmp/ec_test"},
        )
        if use_ec_connector
        else None
    )

    vllm_config = VllmConfig(
        scheduler_config=scheduler_config,
        model_config=model_config,
        cache_config=cache_config,
        parallel_config=ParallelConfig(pipeline_parallel_size=pipeline_parallel_size),
        kv_transfer_config=kv_transfer_config,
        speculative_config=speculative_config,
        ec_transfer_config=ec_transfer_config,
    )
    kv_cache_config = KVCacheConfig(
        num_blocks=num_blocks,  # A large number of blocks to hold all requests
        kv_cache_tensors=[],
        kv_cache_groups=[
            KVCacheGroupSpec(
                ["layer"],
                FullAttentionSpec(
                    block_size=block_size,
                    num_kv_heads=1,
                    head_size=1,
                    dtype=torch.float32,
                ),
            )
        ],
    )
    cache_config.num_gpu_blocks = num_blocks
    scheduler_cls = AsyncScheduler if async_scheduling else Scheduler
    return scheduler_cls(
        vllm_config=vllm_config,
        kv_cache_config=kv_cache_config,
        block_size=block_size,
        log_stats=True,
        structured_output_manager=StructuredOutputManager(vllm_config),
    )