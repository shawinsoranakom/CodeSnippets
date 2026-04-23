def generate_experiment_configs(
    calculate_bwd: bool,
    dtype: torch.dtype,
    batch_sizes: list[int],
    num_heads: list[tuple[int, int]],
    seq_lens: list[int],
    head_dims: list[int],
    score_mods_str: list[str],
    decoding: bool,
    kv_cache_size: list[int],
    cal_bandwidth: bool,
    backends: list[str],
    max_autotune: bool,
) -> list[ExperimentConfig]:
    if calculate_bwd and decoding:
        raise AssertionError("Decoding does not support backward")

    if decoding:
        q_kv_seq_lens = [(1, i) for i in seq_lens]  # only testing query length == 1
    else:
        q_kv_seq_lens = [(i, i) for i in seq_lens]  # only testing q_len == kv_len
    dtypes = [dtype]

    all_configs = []
    for (
        bsz,
        (q_heads, kv_heads),
        (q_seq_len, kv_seq_len),
        head_dim,
        attn_type,
        dtype,
    ) in itertools.product(
        kv_cache_size if kv_cache_size else batch_sizes,
        num_heads,
        q_kv_seq_lens,
        head_dims,
        score_mods_str,
        dtypes,
    ):
        if kv_cache_size:
            head_size_bytes = torch.finfo(dtype).bits / 8 * head_dim
            bsz = int(
                (bsz * 1024 * 1024) // (kv_heads * kv_seq_len * head_size_bytes * 2)
            )
            if bsz <= 0:
                continue

        if q_heads % kv_heads != 0:
            raise AssertionError(
                f"q_heads ({q_heads}) must be divisible by kv_heads ({kv_heads})"
            )

        all_configs.append(
            ExperimentConfig(
                shape=(bsz, q_heads, q_seq_len, kv_heads, kv_seq_len, head_dim),
                attn_type=attn_type,
                dtype=dtype,
                calculate_bwd_time=calculate_bwd,
                cal_bandwidth=cal_bandwidth,
                backends=backends,
                max_autotune=max_autotune,
            )
        )

    return all_configs