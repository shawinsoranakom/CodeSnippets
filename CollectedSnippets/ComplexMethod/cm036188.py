def _create_proposer(
    method: str,
    num_speculative_tokens: int,
    attention_backend: str | None = None,
    speculative_token_tree: list[tuple[int, ...]] | None = None,
    parallel_drafting: bool = False,
) -> EagleProposer:
    # Method-dependent setup
    if method == "eagle":
        target_model_dir = model_dir
        draft_model_dir = eagle_dir
    elif method == "eagle3":
        target_model_dir = model_dir
        draft_model_dir = eagle3_dir
    elif method == "draft_model":
        target_model_dir = model_dir
        draft_model_dir = ar_draft_model_dir
    elif method == "dflash":
        target_model_dir = dflash_target_dir
        draft_model_dir = dflash_dir
    else:
        raise ValueError(f"Unknown method: {method}")

    model_config = ModelConfig(
        model=target_model_dir,
        runner="generate",
        max_model_len=100,
        trust_remote_code=(method == "dflash"),
    )

    spec_token_tree_str = None
    if speculative_token_tree is not None:
        assert num_speculative_tokens == len(speculative_token_tree)
        spec_token_tree_str = str(speculative_token_tree)

    speculative_config = SpeculativeConfig(
        target_model_config=model_config,
        target_parallel_config=ParallelConfig(),
        model=draft_model_dir,
        method=method,
        num_speculative_tokens=num_speculative_tokens,
        speculative_token_tree=spec_token_tree_str,
        parallel_drafting=parallel_drafting,
    )
    if parallel_drafting:
        # Overwrite pard_token to avoid crash during init
        speculative_config.draft_model_config.hf_config.pard_token = 0

    device = DEVICE_TYPE
    vllm_config = VllmConfig(
        model_config=model_config,
        cache_config=CacheConfig(block_size=16),
        speculative_config=speculative_config,
        device_config=DeviceConfig(device=device),
        parallel_config=ParallelConfig(),
        load_config=LoadConfig(),
        scheduler_config=SchedulerConfig(
            max_model_len=model_config.max_model_len,
            is_encoder_decoder=model_config.is_encoder_decoder,
        ),
        attention_config=AttentionConfig(backend=attention_backend),
    )

    if method == "dflash":
        proposer = DFlashProposer(vllm_config=vllm_config, device=device)
    elif "eagle" in method:
        proposer = EagleProposer(vllm_config=vllm_config, device=device)
    else:
        proposer = DraftModelProposer(vllm_config=vllm_config, device=device)
    proposer.block_size = BLOCK_SIZE
    return proposer