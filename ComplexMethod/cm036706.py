def test_varlen_with_paged_kv(
    seq_lens: list[tuple[int, int]],
    num_heads: tuple[int, int],
    head_size: int,
    sliding_window: int | None,
    dtype: torch.dtype,
    block_size: int,
    soft_cap: float | None,
    num_blocks: int,
    q_dtype: torch.dtype | None,
) -> None:
    from vllm._aiter_ops import is_aiter_found_and_supported

    if not is_aiter_found_and_supported():
        pytest.skip("aiter package required for this test.")

    torch.set_default_device("cuda")
    set_random_seed(0)
    num_seqs = len(seq_lens)
    query_lens = [x[0] for x in seq_lens]
    kv_lens = [x[1] for x in seq_lens]
    num_query_heads = num_heads[0]
    num_kv_heads = num_heads[1]
    assert num_query_heads % num_kv_heads == 0
    max_query_len = max(query_lens)
    max_kv_len = max(kv_lens)
    window_size = (sliding_window - 1, 0) if sliding_window is not None else (-1, -1)
    scale = head_size**-0.5

    query = torch.randn(sum(query_lens), num_query_heads, head_size, dtype=dtype)
    key_cache = torch.randn(
        num_blocks, block_size, num_kv_heads, head_size, dtype=dtype
    )
    value_cache = torch.randn_like(key_cache)
    cu_query_lens = torch.tensor([0] + query_lens, dtype=torch.int32).cumsum(
        dim=0, dtype=torch.int32
    )

    cu_seq_lens = torch.tensor([0] + kv_lens, dtype=torch.int32).cumsum(
        dim=0, dtype=torch.int32
    )
    # Save kv_lens as list before converting to tensor
    kv_lens_list = kv_lens
    kv_lens = torch.tensor(kv_lens, dtype=torch.int32)

    max_num_blocks_per_seq = (max_kv_len + block_size - 1) // block_size
    block_tables = torch.randint(
        0, num_blocks, (num_seqs, max_num_blocks_per_seq), dtype=torch.int32
    )

    output = torch.empty_like(query)

    maybe_quantized_query = query
    maybe_quantized_key_cache = key_cache
    maybe_quantized_value_cache = value_cache
    k_scale_tensor = None
    v_scale_tensor = None
    dequant = False

    if q_dtype is not None:
        # QKV are drawn from N(0, 1): no need for a fp8 scaling factor
        maybe_quantized_query = query.to(q_dtype)
        maybe_quantized_key_cache = key_cache.to(q_dtype)
        maybe_quantized_value_cache = value_cache.to(q_dtype)
        dequant = True
        scale_shape = (num_seqs, num_kv_heads)

        # For per-seq-per-head scales (matching AITER backend expectation)
        k_scale_tensor = torch.ones(scale_shape, dtype=torch.float32)
        v_scale_tensor = torch.ones(scale_shape, dtype=torch.float32)

    # Prepare metadata for cp_mha_gather_cache
    # token_to_batch: maps each token to its batch index
    token_to_batch = torch.zeros(sum(kv_lens_list), dtype=torch.int32)
    seq_starts = torch.zeros(num_seqs, dtype=torch.int32)

    token_idx = 0
    for batch_idx, kv_len in enumerate(kv_lens_list):
        token_to_batch[token_idx : token_idx + kv_len] = batch_idx
        seq_starts[batch_idx] = 0  # Assuming all sequences start at 0 in their blocks
        token_idx += kv_len

    # Allocate buffers for gathered KV
    total_kv_tokens = sum(kv_lens_list)
    gathered_key = torch.empty(
        total_kv_tokens, num_kv_heads, head_size, dtype=maybe_quantized_key_cache.dtype
    )
    gathered_value = torch.empty(
        total_kv_tokens,
        num_kv_heads,
        head_size,
        dtype=maybe_quantized_value_cache.dtype,
    )

    # Gather paged KV cache into contiguous tensors using triton kernel
    cp_mha_gather_cache(
        key_cache=maybe_quantized_key_cache,
        value_cache=maybe_quantized_value_cache,
        key=gathered_key,
        value=gathered_value,
        block_tables=block_tables,
        k_scales=k_scale_tensor
        if k_scale_tensor is not None
        else torch.ones(1, dtype=torch.float32),
        v_scales=v_scale_tensor
        if v_scale_tensor is not None
        else torch.ones(1, dtype=torch.float32),
        cu_seqlens_kv=cu_seq_lens,
        token_to_batch=token_to_batch,
        seq_starts=seq_starts,
        dequant=dequant,
        kv_cache_layout="NHD",
        total_tokens=total_kv_tokens,
    )

    # Call aiter flash attention with gathered KV
    aiter.flash_attn_varlen_func(
        q=maybe_quantized_query,
        k=gathered_key,
        v=gathered_value,
        cu_seqlens_q=cu_query_lens,
        cu_seqlens_k=cu_seq_lens,
        max_seqlen_q=max_query_len,
        max_seqlen_k=max_kv_len,
        min_seqlen_q=1,
        dropout_p=0.0,
        softmax_scale=scale,
        causal=True,
        window_size=window_size,
        alibi_slopes=None,
        return_lse=False,
        out=output,
    )

    ref_output = ref_paged_attn(
        query=query,
        key_cache=key_cache,
        value_cache=value_cache,
        query_lens=query_lens,
        kv_lens=kv_lens_list,
        block_tables=block_tables,
        scale=scale,
        sliding_window=sliding_window,
        soft_cap=soft_cap,
    )

    atol, rtol = 2e-2, 2e-2
    if q_dtype is not None:
        atol, rtol = 1.5e-1, 1.5e-1
    (
        torch.testing.assert_close(output, ref_output, atol=atol, rtol=rtol),
        f"{torch.max(torch.abs(output - ref_output))}",
    )

    # Log diff stats for tracking changes
    print(f"Max abs diff: {torch.max(torch.abs(output - ref_output))}")
    print(f"Mean diff: {torch.mean(torch.abs(output - ref_output))}")
    print(f"Min diff: {torch.std(torch.abs(output - ref_output))}")