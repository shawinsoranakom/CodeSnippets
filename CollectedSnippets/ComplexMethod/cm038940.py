def main(
    version: str,
    num_seqs: int,
    seq_len: int,
    num_query_heads: int,
    num_kv_heads: int,
    head_size: int,
    use_alibi: bool,
    block_size: int,
    dtype: torch.dtype,
    seed: int,
    do_profile: bool,
    device: str = "cuda",
    kv_cache_dtype: str | None = None,
) -> None:
    set_random_seed(seed)

    scale = float(1.0 / (head_size**0.5))
    query = torch.empty(
        num_seqs, num_query_heads, head_size, dtype=dtype, device=device
    )
    query.uniform_(-scale, scale)

    assert num_query_heads % num_kv_heads == 0
    alibi_slopes = None
    if use_alibi:
        alibi_slopes = torch.randn(num_query_heads, dtype=torch.float, device=device)

    seq_lens = [seq_len for _ in range(num_seqs)]
    max_seq_len = max(seq_lens)
    seq_lens = torch.tensor(seq_lens, dtype=torch.int, device=device)

    # Create the block tables.
    max_num_blocks_per_seq = (max_seq_len + block_size - 1) // block_size
    block_tables_lst: list[list[int]] = []
    for _ in range(num_seqs):
        block_table = [
            random.randint(0, NUM_BLOCKS - 1) for _ in range(max_num_blocks_per_seq)
        ]
        block_tables_lst.append(block_table)

    block_tables = torch.tensor(block_tables_lst, dtype=torch.int, device=device)

    # Create the KV cache.
    key_caches, value_caches = create_kv_caches_with_random(
        NUM_BLOCKS,
        block_size,
        1,
        num_kv_heads,
        head_size,
        kv_cache_dtype,
        dtype,
        device=device,
    )
    key_cache, value_cache = key_caches[0], value_caches[0]

    # Prepare for the paged attention kernel.
    output = torch.empty_like(query)
    if version == "v2":
        if current_platform.is_rocm():
            global PARTITION_SIZE
            if not args.custom_paged_attn and not current_platform.is_navi():
                PARTITION_SIZE = 1024
            else:
                PARTITION_SIZE = PARTITION_SIZE_ROCM
        num_partitions = (max_seq_len + PARTITION_SIZE - 1) // PARTITION_SIZE
        tmp_output = torch.empty(
            size=(num_seqs, num_query_heads, num_partitions, head_size),
            dtype=output.dtype,
            device=output.device,
        )
        exp_sums = torch.empty(
            size=(num_seqs, num_query_heads, num_partitions),
            dtype=torch.float32,
            device=output.device,
        )
        max_logits = torch.empty_like(exp_sums)

    def run_cuda_benchmark(num_iters: int, profile: bool = False) -> float:
        torch.accelerator.synchronize()
        if profile:
            torch.cuda.cudart().cudaProfilerStart()
        start_time = time.perf_counter()

        # Using default kv_scale
        k_scale = v_scale = torch.tensor(1.0, dtype=torch.float32, device=device)

        for _ in range(num_iters):
            if version == "v1":
                ops.paged_attention_v1(
                    output,
                    query,
                    key_cache,
                    value_cache,
                    num_kv_heads,
                    scale,
                    block_tables,
                    seq_lens,
                    block_size,
                    max_seq_len,
                    alibi_slopes,
                    kv_cache_dtype,
                    k_scale,
                    v_scale,
                )
            elif version == "v2":
                if not args.custom_paged_attn:
                    ops.paged_attention_v2(
                        output,
                        exp_sums,
                        max_logits,
                        tmp_output,
                        query,
                        key_cache,
                        value_cache,
                        num_kv_heads,
                        scale,
                        block_tables,
                        seq_lens,
                        block_size,
                        max_seq_len,
                        alibi_slopes,
                        kv_cache_dtype,
                        k_scale,
                        v_scale,
                    )
                else:
                    ops.paged_attention_rocm(
                        output,
                        exp_sums,
                        max_logits,
                        tmp_output,
                        query,
                        key_cache,
                        value_cache,
                        num_kv_heads,
                        scale,
                        block_tables,
                        seq_lens,
                        None,
                        block_size,
                        max_seq_len,
                        alibi_slopes,
                        kv_cache_dtype,
                        k_scale,
                        v_scale,
                    )
            else:
                raise ValueError(f"Invalid version: {version}")
        torch.accelerator.synchronize()

        end_time = time.perf_counter()
        if profile:
            torch.cuda.cudart().cudaProfilerStop()
        return (end_time - start_time) / num_iters

    # Warmup.
    print("Warming up...")
    run_benchmark = run_cuda_benchmark
    run_benchmark(num_iters=3, profile=False)

    # Benchmark.
    if do_profile:
        latency = run_benchmark(num_iters=1, profile=True)
    else:
        latency = run_benchmark(num_iters=100, profile=False)
    print(f"Kernel running time: {latency * 1000000:.3f} us")