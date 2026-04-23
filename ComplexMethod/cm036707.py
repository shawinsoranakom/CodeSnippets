def test_triton_unified_attn(
    seq_lens: list[tuple[int, int]],
    num_heads: tuple[int, int],
    head_size: int,
    sliding_window: int | None,
    dtype: torch.dtype,
    block_size: int,
    soft_cap: float | None,
    num_blocks: int,
    q_dtype: torch.dtype | None,
    seq_threshold_3D: int,
) -> None:
    torch.set_default_device(DEVICE_TYPE)

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
    kv_lens = torch.tensor(kv_lens, dtype=torch.int32)

    max_num_blocks_per_seq = (max_kv_len + block_size - 1) // block_size
    block_tables = torch.randint(
        0, num_blocks, (num_seqs, max_num_blocks_per_seq), dtype=torch.int32
    )

    output = torch.empty_like(query)

    maybe_quantized_query = query
    maybe_quantized_key_cache = key_cache
    maybe_quantized_value_cache = value_cache
    q_descale = None
    k_descale = None
    v_descale = None
    if q_dtype is not None:
        # QKV are drawn from N(0, 1): no need for a fp8 scaling factor
        maybe_quantized_query = query.to(q_dtype)
        maybe_quantized_key_cache = key_cache.to(q_dtype)
        maybe_quantized_value_cache = value_cache.to(q_dtype)

        scale_shape = (num_seqs, num_kv_heads)
        q_descale = None  # Not yet supported
        k_descale = torch.rand(scale_shape, dtype=torch.float32)
        v_descale = torch.rand(scale_shape, dtype=torch.float32)

    num_par_softmax_segments = 16
    head_size_padded = next_power_of_2(head_size)
    softmax_segm_output = torch.empty(
        (seq_threshold_3D, num_query_heads, num_par_softmax_segments, head_size_padded),
        dtype=torch.float32,
    )
    softmax_segm_max = torch.empty(
        (seq_threshold_3D, num_query_heads, num_par_softmax_segments),
        dtype=torch.float32,
    )
    softmax_segm_expsum = torch.empty(
        (seq_threshold_3D, num_query_heads, num_par_softmax_segments),
        dtype=torch.float32,
    )

    unified_attention(
        q=maybe_quantized_query,
        k=maybe_quantized_key_cache,
        v=maybe_quantized_value_cache,
        out=output,
        cu_seqlens_q=cu_query_lens,
        seqused_k=kv_lens,
        max_seqlen_q=max_query_len,
        max_seqlen_k=max_kv_len,
        softmax_scale=scale,
        causal=True,
        window_size=window_size,
        block_table=block_tables,
        softcap=soft_cap if soft_cap is not None else 0,
        q_descale=q_descale,
        k_descale=k_descale,
        v_descale=v_descale,
        seq_threshold_3D=seq_threshold_3D,
        num_par_softmax_segments=num_par_softmax_segments,
        softmax_segm_output=softmax_segm_output,
        softmax_segm_max=softmax_segm_max,
        softmax_segm_expsum=softmax_segm_expsum,
    )

    ref_output = ref_paged_attn(
        query=query,
        key_cache=key_cache,
        value_cache=value_cache,
        query_lens=query_lens,
        kv_lens=kv_lens,
        block_tables=block_tables,
        scale=scale,
        sliding_window=sliding_window,
        soft_cap=soft_cap,
    )
    atol, rtol = 1.5e-2, 1e-2
    if q_dtype is not None:
        atol, rtol = 1.5e-1, 1.5e-1
    (
        torch.testing.assert_close(output, ref_output, atol=atol, rtol=rtol),
        f"{torch.max(torch.abs(output - ref_output))}",
    )