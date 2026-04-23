def run_mla_benchmark(
    backend: str,
    config,
    reorder_batch_threshold: int | None = None,
    num_kv_splits: int | None = None,
    index_topk: int = 2048,
    prefill_backend: str | None = None,
) -> BenchmarkResult | list[BenchmarkResult]:
    """
    Unified MLA benchmark runner for all backends.

    Works for: flashattn_mla, flashmla, flashinfer_mla, cutlass_mla,
               flashinfer_mla_sparse, flashmla_sparse

    Always uses batched execution internally for optimal performance.

    Args:
        backend: Backend name (flashattn_mla, flashmla, flashinfer_mla, cutlass_mla,
                 flashinfer_mla_sparse, flashmla_sparse)
        config: BenchmarkConfig or list of (BenchmarkConfig, param) tuples
        reorder_batch_threshold: Threshold override for FlashAttn/FlashMLA
                                 (single config mode only)
        num_kv_splits: Number of KV splits for CUTLASS (single config mode only)
        index_topk: Topk value for sparse MLA backends (default 2048)
        prefill_backend: Prefill backend name (e.g., "fa3", "fa4").
            When set, forces the specified FlashAttention version for prefill.

    Returns:
        BenchmarkResult (single mode) or list of BenchmarkResult (batched mode)
    """
    # Normalize to batched mode: (config, threshold, num_splits)
    if isinstance(config, list):
        # Already in batched format
        if len(config) > 0 and isinstance(config[0], tuple):
            # Format: [(cfg, param), ...] where param is threshold or num_splits
            if backend in ("flashattn_mla", "flashmla", "flashmla_sparse"):
                configs_with_params = [(cfg, param, None) for cfg, param in config]
            else:  # cutlass_mla, flashinfer_mla, or sparse backends
                configs_with_params = [(cfg, None, param) for cfg, param in config]
        else:
            # Format: [cfg, ...] - just configs
            configs_with_params = [(cfg, None, None) for cfg in config]
        return_single = False
    else:
        # Single config: convert to batched format
        configs_with_params = [(config, reorder_batch_threshold, num_kv_splits)]
        return_single = True

    # Use unified batched execution
    results = _run_mla_benchmark_batched(
        backend, configs_with_params, index_topk, prefill_backend=prefill_backend
    )

    # Return single result or list based on input
    return results[0] if return_single else results