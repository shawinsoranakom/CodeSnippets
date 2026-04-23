def _run_single_benchmark(
    config,
    impl,
    layer,
    builder_instance,
    backend_cfg: dict,
    mla_dims: dict,
    device: torch.device,
    indexer=None,
    kv_cache_dtype: str | None = None,
) -> BenchmarkResult:
    """
    Run a single benchmark iteration.

    Args:
        config: BenchmarkConfig instance
        impl: Backend implementation instance
        layer: MockLayer instance
        builder_instance: Metadata builder instance
        backend_cfg: Backend configuration dict
        mla_dims: MLA dimension configuration
        device: Target device
        indexer: Optional MockIndexer for sparse backends

    Returns:
        BenchmarkResult with timing statistics
    """
    # Parse batch spec
    requests = parse_batch_spec(config.batch_spec)
    q_lens = [r.q_len for r in requests]
    kv_lens = [r.kv_len for r in requests]
    total_q = sum(q_lens)
    max_kv_len = max(kv_lens)

    # Determine block size
    block_size = backend_cfg["block_size"] or config.block_size

    # Build metadata
    metadata, num_blocks = _build_attention_metadata(
        requests, block_size, device, builder_instance
    )

    # Create KV cache
    if kv_cache_dtype is None:
        kv_cache_dtype = getattr(config, "kv_cache_dtype", "auto")
    head_size = mla_dims["kv_lora_rank"] + mla_dims["qk_rope_head_dim"]
    if kv_cache_dtype == "fp8_ds_mla":
        # FlashMLA sparse custom format: 656 bytes per token, stored as uint8.
        # Layout: kv_lora_rank fp8 bytes + 4 float32 tile scales
        #         + 2*rope_dim bf16 bytes
        # = 512 + 16 + 128 = 656 bytes for DeepSeek dims.
        kv_cache = torch.zeros(
            num_blocks,
            block_size,
            656,
            device=device,
            dtype=torch.uint8,
        )
    elif kv_cache_dtype == "fp8":
        from vllm.platforms import current_platform

        kv_cache = torch.zeros(
            num_blocks,
            block_size,
            head_size,
            device=device,
            dtype=torch.uint8,
        ).view(current_platform.fp8_dtype())
    else:
        kv_cache = torch.zeros(
            num_blocks,
            block_size,
            head_size,
            device=device,
            dtype=torch.bfloat16,
        )

    # Fill indexer with random indices for sparse backends
    is_sparse = backend_cfg.get("is_sparse", False)
    if is_sparse and indexer is not None:
        indexer.fill_random_indices(total_q, max_kv_len)

    # Determine which forward methods to use based on metadata.
    # Sparse MLA backends always use forward_mqa
    has_decode = is_sparse or getattr(metadata, "decode", None) is not None
    has_prefill = not is_sparse and getattr(metadata, "prefill", None) is not None
    if not has_decode and not has_prefill:
        raise RuntimeError("Metadata has neither decode nor prefill metadata")

    num_decode = (
        metadata.num_decode_tokens
        if (has_decode and has_prefill)
        else total_q
        if has_decode
        else 0
    )
    num_prefill = total_q - num_decode

    # Some backends requires fp8 queries when using fp8 KV cache.
    is_fp8_kvcache = kv_cache_dtype.startswith("fp8")
    quantize_query = is_fp8_kvcache and getattr(
        impl, "supports_quant_query_input", False
    )

    # quantize_query forces concat format
    query_fmt = "concat" if quantize_query else backend_cfg["query_format"]

    # Create decode query tensors
    if has_decode:
        decode_inputs, _ = _create_input_tensors(
            num_decode, mla_dims, query_fmt, device, torch.bfloat16
        )
        # Cast decode query to fp8 if the backend supports it
        if quantize_query:
            from vllm.platforms import current_platform

            if isinstance(decode_inputs, tuple):
                decode_inputs = torch.cat(list(decode_inputs), dim=-1)
            decode_inputs = decode_inputs.to(current_platform.fp8_dtype())

    # Create prefill input tensors
    if has_prefill:
        _, prefill_inputs = _create_input_tensors(
            num_prefill, mla_dims, query_fmt, device, torch.bfloat16
        )

    # Build forward function
    def forward_fn():
        results = []
        if has_decode:
            results.append(impl.forward_mqa(decode_inputs, kv_cache, metadata, layer))
        if has_prefill:
            results.append(
                impl.forward_mha(
                    prefill_inputs["q"],
                    prefill_inputs["k_c_normed"],
                    prefill_inputs["k_pe"],
                    kv_cache,
                    metadata,
                    prefill_inputs["k_scale"],
                    prefill_inputs["output"],
                )
            )
        return results[0] if len(results) == 1 else tuple(results)

    # Warmup
    for _ in range(config.warmup_iters):
        forward_fn()
    torch.accelerator.synchronize()

    # Optionally capture a CUDA graph after warmup.
    # Graph replay eliminates CPU launch overhead so timings reflect pure
    # kernel time.
    if config.use_cuda_graphs:
        graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(graph):
            forward_fn()
        benchmark_fn = graph.replay
    else:
        benchmark_fn = forward_fn

    # Benchmark
    times = []
    for _ in range(config.repeats):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)

        start.record()
        for _ in range(config.num_layers):
            benchmark_fn()
        end.record()

        torch.accelerator.synchronize()
        elapsed_ms = start.elapsed_time(end)
        times.append(elapsed_ms / 1000.0 / config.num_layers)

    mean_time = float(np.mean(times))
    return BenchmarkResult(
        config=config,
        mean_time=mean_time,
        std_time=float(np.std(times)),
        min_time=float(np.min(times)),
        max_time=float(np.max(times)),
        throughput_tokens_per_sec=total_q / mean_time if mean_time > 0 else 0,
    )