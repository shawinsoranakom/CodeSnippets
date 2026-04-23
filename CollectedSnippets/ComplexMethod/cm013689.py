def _fa3_run_forward(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    cu_seq_q: torch.Tensor | None,
    cu_seq_k: torch.Tensor | None,
    max_q: int,
    max_k: int,
    scale: float | None,
    is_causal: bool,
    window_size_left: int | None,
    window_size_right: int | None,
    seqused_k: torch.Tensor | None,
    out: torch.Tensor | None = None,
    q_descale: torch.Tensor | None = None,
    k_descale: torch.Tensor | None = None,
    v_descale: torch.Tensor | None = None,
    block_table: torch.Tensor | None = None,
    num_splits: int | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Run the FA3 forward pass by calling the C++ kernel directly.
    """
    if _FA3_CUDA_FWD is None:
        raise RuntimeError("FA3 not registered")
    # Ensure contiguous in the last dimension
    q = _maybe_contiguous(query)
    k = _maybe_contiguous(key)
    v = (
        value.contiguous()
        if value.dtype == torch.float8_e4m3fn
        and value.stride(-1) != 1
        and value.stride(-3) != 1
        else _maybe_contiguous(value)
    )

    cu_seqlens_q = _maybe_contiguous(cu_seq_q)
    cu_seqlens_k = _maybe_contiguous(cu_seq_k)
    seqused_k = _maybe_contiguous(seqused_k)
    block_table = _maybe_contiguous(block_table)

    out, softmax_lse, out_accum, softmax_lse_accum = _FA3_CUDA_FWD(
        q,
        k,
        v,
        None,  # k_new
        None,  # v_new
        None,  # qv
        out,  # out_ (pre-allocated output)
        cu_seqlens_q,  # cu_seqlens_q
        cu_seqlens_k,  # cu_seqlens_k
        None,  # cu_seqlens_k_new
        None,  # seqused_q
        seqused_k,  # seqused_k
        max_q,  # max_seqlen_q
        max_k,  # max_seqlen_k
        block_table,  # block_table,
        None,  # kv_batch_idx,
        None,  # leftpad_k,
        None,  # rotary_cos,
        None,  # rotary_sin,
        None,  # seqlens_rotary,
        q_descale,  # q_descale,
        k_descale,  # k_descale,
        v_descale,  # v_descale,
        scale,  # softmax_scale,
        is_causal,  # causal,
        window_size_left if window_size_left is not None else -1,  # window_size_left
        window_size_right if window_size_right is not None else -1,  # window_size_right
        0,  # attention_chunk,
        0.0,  # softcap,
        True,  # rotary_interleaved,
        None,  # scheduler_metadata,
        num_splits
        or (1 if torch.are_deterministic_algorithms_enabled() else 0),  # num_splits,
        None,  # pack_gqa,
        torch._C._get_sm_carveout_experimental() or 0,  # sm_margin,
    )
    return out, softmax_lse.contiguous()