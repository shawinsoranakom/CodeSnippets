def test_paged_attention(
    kv_cache_factory,
    version: str,
    num_seqs: int,
    num_heads: tuple[int, int],
    head_size: int,
    use_alibi: bool,
    block_size: int,
    dtype: torch.dtype,
    kv_cache_dtype: str,
    seed: int,
    device: str,
) -> None:
    if (kv_cache_dtype == "fp8" and head_size % 16) or (
        version == "rocm" and head_size not in (64, 128)
    ):
        pytest.skip()

    if (
        version == "rocm"
        and current_platform.is_navi()
        and (
            kv_cache_dtype == "fp8" or head_size != 128 or block_size != 16 or use_alibi
        )
    ):
        pytest.skip()

    global PARTITION_SIZE

    set_random_seed(seed)
    torch.set_default_device(device)
    scale = float(1.0 / (head_size**0.5))
    num_query_heads, num_kv_heads = num_heads
    query = torch.empty(num_seqs, num_query_heads, head_size, dtype=dtype)
    query.uniform_(-scale, scale)

    assert num_query_heads % num_kv_heads == 0
    num_queries_per_kv = num_query_heads // num_kv_heads
    alibi_slopes = None
    if use_alibi:
        alibi_slopes = torch.randn(num_query_heads, dtype=torch.float)

    seq_lens = [random.randint(1, MAX_SEQ_LEN) for _ in range(num_seqs)]
    seq_lens[-1] = MAX_SEQ_LEN
    max_seq_len = max(seq_lens)
    seq_lens = torch.tensor(seq_lens, dtype=torch.int)

    # Create the block tables.
    max_num_blocks_per_seq = (max_seq_len + block_size - 1) // block_size
    block_tables_lst: list[list[int]] = []
    for _ in range(num_seqs):
        block_table = [
            random.randint(0, NUM_BLOCKS - 1) for _ in range(max_num_blocks_per_seq)
        ]
        block_tables_lst.append(block_table)

    block_tables = torch.tensor(block_tables_lst, dtype=torch.int)

    # Create the KV caches.
    key_caches, value_caches = kv_cache_factory(
        NUM_BLOCKS,
        block_size,
        1,
        num_kv_heads,
        head_size,
        kv_cache_dtype,
        dtype,
        seed,
        device,
    )
    key_cache, value_cache = key_caches[0], value_caches[0]

    # Using default kv_scale
    k_scale = v_scale = torch.tensor(1.0, dtype=torch.float32, device=device)

    # Call the paged attention kernel.
    output = torch.empty_like(query)
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

        opcheck(
            torch.ops._C.paged_attention_v1,
            (
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
                0,
                0,
                0,
                64,
                0,
            ),
            cond=(head_size == HEAD_SIZES[0] and block_size == BLOCK_SIZES[0]),
        )

    elif version in ("v2", "rocm"):
        if current_platform.is_rocm() and version == "rocm":
            PARTITION_SIZE = PARTITION_SIZE_ROCM

        num_partitions = (max_seq_len + PARTITION_SIZE - 1) // PARTITION_SIZE
        assert PARTITION_SIZE % block_size == 0
        num_seqs, num_heads, head_size = output.shape
        tmp_output = torch.empty(
            size=(num_seqs, num_heads, num_partitions, head_size),
            dtype=output.dtype,
        )
        exp_sums = torch.empty(
            size=(num_seqs, num_heads, num_partitions),
            dtype=torch.float32,
        )
        max_logits = torch.empty_like(exp_sums)
        if version == "v2":
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

            opcheck(
                torch.ops._C.paged_attention_v2,
                (
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
                    0,
                    0,
                    0,
                    64,
                    0,
                ),
                cond=(head_size == HEAD_SIZES[0] and block_size == BLOCK_SIZES[0]),
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

            opcheck(
                torch.ops._rocm_C.paged_attention,
                (
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
                ),
                cond=(head_size == HEAD_SIZES[0] and block_size == BLOCK_SIZES[0]),
            )

    else:
        raise AssertionError(f"Unknown version: {version}")

    # Run the reference implementation.
    if kv_cache_dtype == "fp8":
        # Convert cache data back to dtype.
        x = 16 // torch.tensor([], dtype=dtype).element_size()
        key_cache_shape = (NUM_BLOCKS, num_kv_heads, head_size // x, block_size, x)
        dequantized_key_cache = torch.empty(
            size=key_cache_shape, dtype=dtype, device=device
        )
        ops.convert_fp8(dequantized_key_cache, key_cache)
        key_cache = dequantized_key_cache

        value_cache_shape = value_cache.shape
        dequantized_value_cache = torch.empty(
            size=value_cache_shape, dtype=dtype, device=device
        )
        ops.convert_fp8(dequantized_value_cache, value_cache)
        value_cache = dequantized_value_cache

    ref_output = torch.empty_like(query)
    ref_single_query_cached_kv_attention(
        ref_output,
        query,
        num_queries_per_kv,
        key_cache,
        value_cache,
        block_tables,
        seq_lens,
        scale,
        alibi_slopes,
    )

    # NOTE(woosuk): Due to the kernel-level differences in the two
    # implementations, there is a small numerical difference in the two
    # outputs. Thus, we use a relaxed tolerance for the test.
    atol = get_default_atol(output) if current_platform.is_rocm() else 1e-3
    rtol = get_default_rtol(output) if current_platform.is_rocm() else 1e-5

    # NOTE(zhaoyang): FP8 KV Cache will introduce quantization error,
    # so we use a relaxed tolerance for the test.
    atol, rtol = 1e-3, 1e-5
    if kv_cache_dtype == "fp8":
        atol, rtol = 1e-2, 1e-5
    torch.testing.assert_close(output, ref_output, atol=atol, rtol=rtol)