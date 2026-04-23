def unified_attention(
    q,
    k,
    v,
    out,
    cu_seqlens_q,
    max_seqlen_q,
    seqused_k,
    max_seqlen_k,
    softmax_scale,
    causal,
    window_size,
    block_table,
    softcap,
    q_descale,
    k_descale,
    v_descale,
    seq_threshold_3D=None,
    num_par_softmax_segments=None,
    softmax_segm_output=None,
    softmax_segm_max=None,
    softmax_segm_expsum=None,
    alibi_slopes=None,
    output_scale=None,
    qq_bias=None,
    # Optional tensor for sinks
    sinks=None,
    # Optional tensor for prefix lengths (PrefixLM support)
    mm_prefix_range=None,
    use_alibi_sqrt=False,
    # KV cache quantization mode and per-token-head scale caches.
    kv_quant_mode: KVQuantMode = KVQuantMode.NONE,
    k_scale_cache=None,  # [num_blocks, block_size, num_kv_heads] float32
    v_scale_cache=None,  # [num_blocks, block_size, num_kv_heads] float32
    # Chunked attention: restrict attention to aligned blocks with lookback.
    chunk_lookback=-1,
):
    assert causal, "Only causal attention is supported"
    assert q_descale is None, "Q scales not supported"

    if sinks is not None:
        assert sinks.shape[0] == q.shape[1], "Sinks must be num_query_heads size"

    use_mm_prefix = False
    max_mm_ranges = 0
    if mm_prefix_range is not None:
        if mm_prefix_range.ndim == 3:
            use_mm_prefix = True
            max_mm_ranges = mm_prefix_range.shape[1]
        else:
            raise ValueError(
                f"Unsupported mm_prefix_range shape: {mm_prefix_range.shape}"
            )

    use_alibi_slopes = alibi_slopes is not None
    use_qq_bias = qq_bias is not None

    block_size = v.shape[1]
    num_seqs = len(seqused_k)
    num_query_heads = q.shape[1]
    num_kv_heads = k.shape[2]
    num_queries_per_kv = num_query_heads // num_kv_heads
    head_size = q.shape[2]

    BLOCK_M = (
        16 if num_queries_per_kv <= 16 else triton.next_power_of_2(num_queries_per_kv)
    )
    BLOCK_Q = BLOCK_M // num_queries_per_kv

    # Ideally we would launch with kernel with:
    # \sum_i[ceil(query_len[i] / BLOCK_Q)] blocks.
    # However, it is slow to realize the query_lens on cpu.
    # Instead we use upper-bound:
    # \sum_i[ceil(query_len[i] / BLOCK_Q)]
    #   <= \sum_i[floor(query_len[i] / BLOCK_Q) + 1]
    #    = \sum_i[floor(query_len[i] / BLOCK_Q)] + num_seqs
    #   <= floor(\sum_i(query_len[i]) / BLOCK_Q) + num_seqs
    #    = floor(q.shape[0] / BLOCK_Q) + num_seqs
    total_num_q_blocks = q.shape[0] // BLOCK_Q + num_seqs

    # Tile sizes for prefill and decode. Gemma3 models use optimized values.
    # Note: tile size must be at least 32 for fp8 (element_size == 1).
    sliding_window_val = 1 + window_size[0] if window_size[0] >= 0 else 0

    # Compute chunked block size from sliding window if needed.
    chunk_size = -1
    if sliding_window_val > 0 and chunk_lookback > -1:
        chunk_size = sliding_window_val // (chunk_lookback + 1)
        assert chunk_size > 0, "sliding_window must be > chunk_lookback+1"
    elif sliding_window_val <= 0:
        chunk_lookback = -1

    TILE_SIZE_PREFILL = _get_tile_size(
        head_size,
        sliding_window_val,
        q.element_size(),
        is_prefill=True,
    )
    TILE_SIZE_DECODE = _get_tile_size(
        head_size,
        sliding_window_val,
        q.element_size(),
        is_prefill=False,
    )

    # Launch the 2D kernel if
    # 1. No intermediate tiled softmax buffers for the 3D kernel have been allocated, or
    # 2. The batch includes at least one prefill request, or
    # 3. The number of sequences exceeds the configured threshold, or
    # 4. Batch invariance is enabled
    if (
        seq_threshold_3D is None
        or num_par_softmax_segments is None
        or softmax_segm_output is None
        or softmax_segm_max is None
        or softmax_segm_expsum is None
        or max_seqlen_q > 1
        or num_seqs > seq_threshold_3D
        or is_batch_invariant
    ):
        kernel_unified_attention_2d[
            (
                total_num_q_blocks,
                num_kv_heads,
            )
        ](
            output_ptr=out,
            query_ptr=q,
            key_cache_ptr=k,
            value_cache_ptr=v,
            sink_ptr=sinks,
            block_tables_ptr=block_table,
            seq_lens_ptr=seqused_k,
            alibi_slopes_ptr=alibi_slopes,
            qq_bias_ptr=qq_bias,
            scale=softmax_scale,
            k_scale=k_descale,
            v_scale=v_descale,
            out_scale=1 / output_scale if output_scale is not None else 1.0,
            softcap=softcap,
            num_query_heads=num_query_heads,
            num_queries_per_kv=num_queries_per_kv,
            block_table_stride=block_table.stride(0),
            query_stride_0=q.stride(0),
            query_stride_1=q.stride(1),
            output_stride_0=out.stride(0),
            output_stride_1=out.stride(1),
            qq_bias_stride_0=qq_bias.stride(0) if use_qq_bias else 0,
            BLOCK_SIZE=block_size,
            TILE_SIZE=TILE_SIZE_PREFILL,
            HEAD_SIZE=head_size,
            HEAD_SIZE_PADDED=triton.next_power_of_2(head_size),
            USE_ALIBI_SLOPES=use_alibi_slopes,
            USE_ALIBI_SQRT=use_alibi_sqrt,
            USE_QQ_BIAS=use_qq_bias,
            USE_SOFTCAP=(softcap > 0),
            USE_SINKS=(sinks is not None),
            USE_MM_PREFIX=use_mm_prefix,
            MAX_MM_RANGES=max_mm_ranges,
            mm_prefix_range_ptr=mm_prefix_range,
            SLIDING_WINDOW=(1 + window_size[0]),
            stride_k_cache_0=k.stride(0),
            stride_k_cache_1=k.stride(1),
            stride_k_cache_2=k.stride(2),
            stride_k_cache_3=k.stride(3),
            stride_v_cache_0=v.stride(0),
            stride_v_cache_1=v.stride(1),
            stride_v_cache_2=v.stride(2),
            stride_v_cache_3=v.stride(3),
            query_start_len_ptr=cu_seqlens_q,
            BLOCK_Q=BLOCK_Q,
            num_seqs=num_seqs,
            BLOCK_M=BLOCK_M,
            USE_FP8=output_scale is not None,
            KV_QUANT_MODE=kv_quant_mode,
            k_scale_cache_ptr=k_scale_cache,
            v_scale_cache_ptr=v_scale_cache,
            stride_ks_blk=k_scale_cache.stride(0) if k_scale_cache is not None else 0,
            stride_ks_slot=k_scale_cache.stride(1) if k_scale_cache is not None else 0,
            stride_ks_head=k_scale_cache.stride(2) if k_scale_cache is not None else 0,
            stride_vs_blk=v_scale_cache.stride(0) if v_scale_cache is not None else 0,
            stride_vs_slot=v_scale_cache.stride(1) if v_scale_cache is not None else 0,
            stride_vs_head=v_scale_cache.stride(2) if v_scale_cache is not None else 0,
            CHUNK_LOOKBACK=chunk_lookback,
            CHUNK_SIZE=chunk_size,
        )
    else:
        kernel_unified_attention_3d[
            (total_num_q_blocks, num_kv_heads, num_par_softmax_segments)
        ](
            segm_output_ptr=softmax_segm_output,
            segm_max_ptr=softmax_segm_max,
            segm_expsum_ptr=softmax_segm_expsum,
            query_ptr=q,
            key_cache_ptr=k,
            value_cache_ptr=v,
            sink_ptr=sinks,
            block_tables_ptr=block_table,
            seq_lens_ptr=seqused_k,
            alibi_slopes_ptr=alibi_slopes,
            qq_bias_ptr=qq_bias,
            scale=softmax_scale,
            k_scale=k_descale,
            v_scale=v_descale,
            softcap=softcap,
            num_query_heads=num_query_heads,
            num_queries_per_kv=num_queries_per_kv,
            block_table_stride=block_table.stride(0),
            query_stride_0=q.stride(0),
            query_stride_1=q.stride(1),
            qq_bias_stride_0=qq_bias.stride(0) if use_qq_bias else 0,
            BLOCK_SIZE=block_size,
            TILE_SIZE=TILE_SIZE_DECODE,
            HEAD_SIZE=head_size,
            HEAD_SIZE_PADDED=triton.next_power_of_2(head_size),
            USE_ALIBI_SLOPES=use_alibi_slopes,
            USE_ALIBI_SQRT=use_alibi_sqrt,
            USE_QQ_BIAS=use_qq_bias,
            USE_SOFTCAP=(softcap > 0),
            USE_SINKS=(sinks is not None),
            USE_MM_PREFIX=use_mm_prefix,
            MAX_MM_RANGES=max_mm_ranges,
            mm_prefix_range_ptr=mm_prefix_range,
            SLIDING_WINDOW=(1 + window_size[0]),
            stride_k_cache_0=k.stride(0),
            stride_k_cache_1=k.stride(1),
            stride_k_cache_2=k.stride(2),
            stride_k_cache_3=k.stride(3),
            stride_v_cache_0=v.stride(0),
            stride_v_cache_1=v.stride(1),
            stride_v_cache_2=v.stride(2),
            stride_v_cache_3=v.stride(3),
            query_start_len_ptr=cu_seqlens_q,
            BLOCK_Q=BLOCK_Q,
            num_seqs=num_seqs,
            BLOCK_M=BLOCK_M,
            NUM_SEGMENTS_PER_SEQ=num_par_softmax_segments,
            KV_QUANT_MODE=kv_quant_mode,
            k_scale_cache_ptr=k_scale_cache,
            v_scale_cache_ptr=v_scale_cache,
            stride_ks_blk=k_scale_cache.stride(0) if k_scale_cache is not None else 0,
            stride_ks_slot=k_scale_cache.stride(1) if k_scale_cache is not None else 0,
            stride_ks_head=k_scale_cache.stride(2) if k_scale_cache is not None else 0,
            stride_vs_blk=v_scale_cache.stride(0) if v_scale_cache is not None else 0,
            stride_vs_slot=v_scale_cache.stride(1) if v_scale_cache is not None else 0,
            stride_vs_head=v_scale_cache.stride(2) if v_scale_cache is not None else 0,
            CHUNK_LOOKBACK=chunk_lookback,
            CHUNK_SIZE=chunk_size,
        )
        reduce_segments[(q.shape[0], num_query_heads)](
            output_ptr=out,
            segm_output_ptr=softmax_segm_output,
            segm_max_ptr=softmax_segm_max,
            segm_expsum_ptr=softmax_segm_expsum,
            seq_lens_ptr=seqused_k,
            num_seqs=num_seqs,
            num_query_heads=num_query_heads,
            out_scale_inv=1 / output_scale if output_scale is not None else 1.0,
            output_stride_0=out.stride(0),
            output_stride_1=out.stride(1),
            block_table_stride=block_table.stride(0),
            TILE_SIZE=TILE_SIZE_DECODE,
            HEAD_SIZE=head_size,
            HEAD_SIZE_PADDED=triton.next_power_of_2(head_size),
            query_start_len_ptr=cu_seqlens_q,
            BLOCK_Q=BLOCK_Q,
            NUM_SEGMENTS_PER_SEQ=num_par_softmax_segments,
            USE_FP8=output_scale is not None,
        )