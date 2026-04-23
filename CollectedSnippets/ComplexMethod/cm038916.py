def run_benchmark(
    num_tokens: int,
    num_heads: int,
    head_size: int,
    block_size: int,
    num_blocks: int,
    dtype: torch.dtype,
    kv_cache_dtype: str,
    kv_cache_layout: str,
    num_iters: int,
    implementation: str,
    benchmark_mode: str,
    device: str = "cuda",
) -> float:
    """Return latency (seconds) for given num_tokens."""

    if kv_cache_dtype == "fp8" and head_size % 16:
        raise ValueError("fp8 kv-cache requires head_size to be a multiple of 16.")

    if implementation not in ("cuda", "triton"):
        raise ValueError(
            f"Unsupported implementation: {implementation}. "
            "Only 'cuda' and 'triton' are supported."
        )
    if implementation == "triton" and kv_cache_layout == "HND":
        return float("nan")  # Triton does not support HND layout yet.

    set_random_seed(42)
    torch.set_default_device(device)

    # create random key / value tensors [T, H, D].
    key = torch.randn(num_tokens, num_heads, head_size, dtype=dtype, device=device)
    value = torch.randn_like(key)

    # prepare the slot mapping.
    # each token is assigned a unique slot in the KV-cache.
    num_slots = block_size * num_blocks
    if num_tokens > num_slots:
        raise ValueError("num_tokens cannot exceed the total number of cache slots")
    slot_mapping_lst = random.sample(range(num_slots), num_tokens)
    slot_mapping = torch.tensor(slot_mapping_lst, dtype=torch.long, device=device)

    key_caches, value_caches = create_kv_caches_with_random_flash(
        num_blocks,
        block_size,
        1,  # num_layers
        num_heads,
        head_size,
        kv_cache_dtype,
        dtype,
        device=device,
        cache_layout=kv_cache_layout,
    )
    key_cache, value_cache = key_caches[0], value_caches[0]
    # to free unused memory
    del key_caches, value_caches

    # compute per-kernel scaling factors for fp8 conversion (if used).
    k_scale = (key.amax() / 64.0).to(torch.float32)
    v_scale = (value.amax() / 64.0).to(torch.float32)

    if implementation == "cuda":
        function_under_test = lambda: ops.reshape_and_cache_flash(
            key,  # noqa: F821
            value,  # noqa: F821
            key_cache,  # noqa: F821
            value_cache,  # noqa: F821
            slot_mapping,  # noqa: F821
            kv_cache_dtype,
            k_scale,
            v_scale,
        )
    else:
        function_under_test = lambda: triton_reshape_and_cache_flash(
            key,  # noqa: F821
            value,  # noqa: F821
            key_cache,  # noqa: F821
            value_cache,  # noqa: F821
            slot_mapping,  # noqa: F821
            kv_cache_dtype,
            k_scale,
            v_scale,
        )
    if benchmark_mode == "cudagraph":
        g = torch.cuda.CUDAGraph()
        with torch.cuda.graph(g):
            function_under_test()
        torch.accelerator.synchronize()
        function_under_test = lambda: g.replay()

    def run_cuda_benchmark(n_iters: int) -> float:
        nonlocal key, value, key_cache, value_cache, slot_mapping
        torch.accelerator.synchronize()
        start = time.perf_counter()
        for _ in range(n_iters):
            function_under_test()
            torch.accelerator.synchronize()
        end = time.perf_counter()
        return (end - start) / n_iters

    # warm-up
    run_cuda_benchmark(3)

    lat = run_cuda_benchmark(num_iters)

    # free tensors to mitigate OOM when sweeping
    del key, value, key_cache, value_cache, slot_mapping
    torch.accelerator.empty_cache()

    return lat