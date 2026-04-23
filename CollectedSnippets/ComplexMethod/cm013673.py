def _varlen_attn(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    cu_seq_q: torch.Tensor,
    cu_seq_k: torch.Tensor | None,
    max_q: int,
    max_k: int,
    is_causal: bool = False,
    scale: float | None = None,
    window_size: list[int] | None = None,
    enable_gqa: bool = False,
    seqused_k: torch.Tensor | None = None,
    block_table: torch.Tensor | None = None,
    num_splits: int | None = None,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Private custom op for variable-length attention.

    This is the internal implementation. Users should use the public varlen_attn function instead.
    """
    window_size = _normalize_window_size(window_size)

    use_cudnn = query.is_cuda and _should_use_cudnn(query.device.index)

    if use_cudnn:
        log.info("Using cuDNN backend for varlen_attn")

        if enable_gqa:
            # TODO: check this
            raise RuntimeError("GQA is not supported with the cuDNN backend.")
        if num_splits is not None:
            # TODO: check this
            raise RuntimeError("num_splits is not supported with the cuDNN backend.")
        if window_size[0] != -1 or window_size[1] != -1:
            raise RuntimeError(
                "cuDNN backend does not support window attention. Please use Flash Attention backend."
            )
        if seqused_k is not None or block_table is not None:
            # TODO: cuDNN supports per-sequence KV lengths via SEQ_LEN_KV + padding_mask,
            # but _cudnn_attention_forward doesn't expose it yet.
            raise RuntimeError(
                "seqused_k/block_table is not yet supported with the cuDNN backend."
            )

        result = torch.ops.aten._cudnn_attention_forward(
            query,
            key,
            value,
            None,  # attn_bias
            cu_seq_q,
            cu_seq_k,
            max_q,
            max_k,
            True,  # compute_log_sumexp
            0.0,  # dropout_p hardcoded to 0.0
            is_causal,
            False,  # return_debug_mask
            scale=scale,
        )
        # cuDNN returns: (output, logsumexp, cum_seq_q, cum_seq_k, max_q, max_k, philox_seed, philox_offset, debug_attn_mask)
        output, softmax_lse, rng_state = result[0], result[1], result[6]
    else:
        log.info("Using Flash Attention backend for varlen_attn")
        output, softmax_lse, rng_state, _, _ = torch.ops.aten._flash_attention_forward(
            query,
            key,
            value,
            cu_seq_q,
            cu_seq_k,
            max_q,
            max_k,
            0.0,  # dropout_p hardcoded to 0.0
            is_causal,
            return_debug_mask=False,
            scale=scale,
            window_size_left=window_size[0],
            window_size_right=window_size[1],
            seqused_k=seqused_k,
            block_table=block_table,
            num_splits=num_splits,
        )

    rng_state_ = torch.zeros(
        (2,), dtype=torch.uint64, device=query.device
    )  # hardcoded since dropout is hardcoded to 0
    return output, softmax_lse, rng_state_