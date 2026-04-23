def _run_mla_benchmark_batched(
    backend: str,
    configs_with_params: list[tuple],  # [(config, threshold, num_splits), ...]
    index_topk: int = 2048,
    prefill_backend: str | None = None,
) -> list[BenchmarkResult]:
    """
    Unified batched MLA benchmark runner for all backends.

    Works for: flashattn_mla, flashmla, flashinfer_mla, cutlass_mla,
               flashinfer_mla_sparse, flashmla_sparse

    This function reuses backend initialization across multiple benchmarks
    to avoid setup/teardown overhead.

    Args:
        backend: Backend name (decode backend used for impl construction)
        configs_with_params: List of (config, threshold, num_splits) tuples
            - threshold: reorder_batch_threshold (FlashAttn/FlashMLA only)
            - num_splits: num_kv_splits (CUTLASS only)
        index_topk: Topk value for sparse MLA backends (default 2048)
        prefill_backend: Prefill backend name (e.g., "fa3", "fa4").
            When set, forces the specified FlashAttention version for prefill.

    Returns:
        List of BenchmarkResult objects
    """
    if not configs_with_params:
        return []

    backend_cfg = _get_backend_config(backend)
    device = torch.device(configs_with_params[0][0].device)
    torch.accelerator.set_device_index(device)

    # Determine block size
    config_block_size = configs_with_params[0][0].block_size
    block_size = backend_cfg["block_size"] or config_block_size

    # Extract MLA dimensions from the first config
    first_config = configs_with_params[0][0]
    mla_dims = _extract_mla_dims_from_config(first_config)

    # If config didn't provide MLA dims, fall back to default model
    if mla_dims is None:
        mla_dims = setup_mla_dims("deepseek-v3")

    # Determine if this is a sparse backend
    is_sparse = backend_cfg.get("is_sparse", False)

    # Extract kv_cache_dtype from the first config
    kv_cache_dtype = getattr(first_config, "kv_cache_dtype", "auto")

    # FlashMLA sparse only supports "fp8_ds_mla" internally (not generic "fp8").
    # Remap here so the user can pass --kv-cache-dtype fp8 regardless of backend.
    if backend.upper() == "FLASHMLA_SPARSE" and kv_cache_dtype == "fp8":
        kv_cache_dtype = "fp8_ds_mla"

    # Compute max total_q across all configs so the metadata builder buffer
    # and scheduler config are large enough for all batch specs.
    max_total_q = max(
        sum(r.q_len for r in parse_batch_spec(cfg.batch_spec))
        for cfg, *_ in configs_with_params
    )

    # Create and set vLLM config for MLA (reused across all benchmarks)
    vllm_config = create_minimal_vllm_config(
        model_name="deepseek-v3",  # Used only for model path
        block_size=block_size,
        max_num_batched_tokens=max_total_q,
        mla_dims=mla_dims,  # Use custom dims from config or default
        index_topk=index_topk if is_sparse else None,
        prefill_backend=prefill_backend,
        kv_cache_dtype=kv_cache_dtype,
    )

    results = []

    with set_current_vllm_config(vllm_config):
        # Clear cached prefill backend detection functions so they re-evaluate
        # with the current VllmConfig. These are @functools.cache decorated and
        # would otherwise return stale results from a previous backend's config.
        from vllm.model_executor.layers.attention.mla_attention import (
            use_cudnn_prefill,
            use_flashinfer_prefill,
            use_trtllm_ragged_deepseek_prefill,
        )

        use_flashinfer_prefill.cache_clear()
        use_cudnn_prefill.cache_clear()
        use_trtllm_ragged_deepseek_prefill.cache_clear()

        # Create backend impl, layer, builder, and indexer (reused across benchmarks)
        impl, layer, builder_instance, indexer = _create_backend_impl(
            backend_cfg,
            mla_dims,
            vllm_config,
            device,
            max_num_tokens=max_total_q,
            index_topk=index_topk if is_sparse else None,
            kv_cache_dtype=kv_cache_dtype,
        )

        # Verify the actual prefill backend matches what was requested
        if prefill_backend is not None:
            prefill_cfg = get_prefill_backend_config(prefill_backend)
            fa_version = prefill_cfg["flash_attn_version"]

            if fa_version is not None:
                # FA backend: verify the impl's FA version
                actual_fa_version = getattr(impl, "vllm_flash_attn_version", None)
                if actual_fa_version != fa_version:
                    raise RuntimeError(
                        f"Prefill backend '{prefill_backend}' requested FA "
                        f"version {fa_version}, but the impl is using FA "
                        f"version {actual_fa_version}. Check "
                        f"vllm/v1/attention/backends/fa_utils.py."
                    )
            else:
                # Non-FA backend: verify the builder picked the right path
                expected_flags = {
                    "flashinfer": "_use_fi_prefill",
                    "cudnn": "_use_cudnn_prefill",
                    "trtllm": "_use_trtllm_ragged_prefill",
                }
                flag_name = expected_flags.get(prefill_backend)
                if flag_name and not getattr(builder_instance, flag_name, False):
                    raise RuntimeError(
                        f"Prefill backend '{prefill_backend}' was requested "
                        f"but the metadata builder did not enable it. This "
                        f"usually means a dependency is missing (e.g., "
                        f"flashinfer not installed) or the platform doesn't "
                        f"support it."
                    )

        # Run each benchmark with the shared impl
        for config, threshold, num_splits in configs_with_params:
            # Set threshold for this benchmark (FlashAttn/FlashMLA only)
            original_threshold = None
            if threshold is not None and builder_instance:
                original_threshold = builder_instance.reorder_batch_threshold
                builder_instance.reorder_batch_threshold = threshold

            # Set num_splits for CUTLASS
            original_num_splits = None
            if num_splits is not None and hasattr(impl, "_num_kv_splits"):
                original_num_splits = impl._num_kv_splits
                impl._num_kv_splits = num_splits

            try:
                result = _run_single_benchmark(
                    config,
                    impl,
                    layer,
                    builder_instance,
                    backend_cfg,
                    mla_dims,
                    device,
                    indexer=indexer,
                    kv_cache_dtype=kv_cache_dtype,
                )
                results.append(result)

            finally:
                # Restore original threshold
                if original_threshold is not None:
                    builder_instance.reorder_batch_threshold = original_threshold

                # Restore original num_splits
                if original_num_splits is not None:
                    impl._num_kv_splits = original_num_splits

    return results