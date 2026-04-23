def run_attention(
    *,
    config: AttentionConfig,
    context: AttentionContext,
    Q: Tensor,
    K: Tensor,
    V: Tensor,
) -> Tensor:
    """
    Run attention using config / context info.

    Backend choice is prioritized for speed: FlashAttention when installed
    (`flash_varlen` for packed/variable-length inputs with `seq_info`, otherwise dense
    flash), then xFormers if flash is unavailable, with PyTorch SDPA as the final
    fallback (e.g., CPU or no fused kernels).

    Varlen flash is preferred when packing metadata is present because it avoids padding
    and keeps peak memory low. xFormers and SDPA can also handle packed batches (we
    pass a block-diagonal mask into each).
    """

    backend = config.backend
    if backend == FLASH_VARLEN and context.seq_info is None:
        backend = FLASH_DENSE if HAS_FLASH_ATTENTION else SDPA

    # [TODO] Flash attention does not support arbitrary attention masks (only
    # causal via flag). When a padding mask is present (e.g. left-padded
    # batched generation), fall back to SDPA which consumes attn_mask.
    # xFormers also does not thread context.attention_mask through, so the
    # same fallback applies.
    if context.attention_mask is not None and backend in (
        FLASH_DENSE,
        FLASH_VARLEN,
        XFORMERS,
    ):
        backend = SDPA

    flash_dense_kwargs = config.flash_dense_kwargs or {}
    flash_varlen_kwargs = config.flash_varlen_kwargs or {}
    sdpa_kwargs = config.sdpa_kwargs or {}
    xformers_kwargs = config.xformers_kwargs or {}

    bsz = context.bsz
    n_heads = context.n_heads
    q_len = context.q_len
    head_dim = context.head_dim
    kv_seq_len = context.kv_seq_len
    requires_grad = context.requires_grad
    sliding_window = context.sliding_window

    if backend == FLASH_VARLEN:
        Q_f = Q.transpose(1, 2).reshape(bsz * q_len, n_heads, head_dim)
        K_f = K.transpose(1, 2).reshape(bsz * q_len, config.n_kv_heads, head_dim)
        V_f = V.transpose(1, 2).reshape(bsz * q_len, config.n_kv_heads, head_dim)
        _, cu_seqlens, max_seqlen = context.seq_info
        return flash_attn_varlen_func(
            Q_f,
            K_f,
            V_f,
            cu_seqlens,
            cu_seqlens,
            max_seqlen,
            max_seqlen,
            **flash_varlen_kwargs,
        ).view(bsz, q_len, n_heads, head_dim)
    elif backend == FLASH_DENSE:
        Q_t = Q.transpose(1, 2)
        K_t = K.transpose(1, 2)
        V_t = V.transpose(1, 2)
        return flash_attn_func(Q_t, K_t, V_t, **flash_dense_kwargs).reshape(
            bsz, q_len, n_heads, head_dim
        )
    elif backend == XFORMERS:
        attn_bias = build_xformers_block_causal_mask(
            context.seq_info,
            sliding_window = sliding_window,
            base_mask = context.causal_mask,
        )

        Q_t = Q.transpose(1, 2)
        K_t = K.transpose(1, 2)
        V_t = V.transpose(1, 2)

        K_mod = K_t
        V_mod = V_t
        Q_mod = Q_t

        if config.n_groups != 1:
            K_mod = K_t.view(bsz, kv_seq_len, config.n_kv_heads, 1, head_dim)
            V_mod = V_t.view(bsz, kv_seq_len, config.n_kv_heads, 1, head_dim)
            K_mod = K_mod.expand(
                bsz, kv_seq_len, config.n_kv_heads, config.n_groups, head_dim
            )
            V_mod = V_mod.expand(
                bsz, kv_seq_len, config.n_kv_heads, config.n_groups, head_dim
            )

            if requires_grad:
                K_mod = K_mod.reshape(bsz, kv_seq_len, n_heads, head_dim)
                V_mod = V_mod.reshape(bsz, kv_seq_len, n_heads, head_dim)
            else:
                Q_mod = Q_t.view(
                    bsz, q_len, config.n_kv_heads, config.n_groups, head_dim
                )

        has_block = XFORMERS_BLOCK_DIAG_CLS is not None and isinstance(
            attn_bias, XFORMERS_BLOCK_DIAG_CLS
        )

        if config.n_groups != 1 and has_block:
            if not requires_grad:
                Q_mod = Q_mod.view(
                    1, bsz * q_len, config.n_kv_heads, config.n_groups, head_dim
                )
                K_mod = K_mod.view(
                    1, bsz * kv_seq_len, config.n_kv_heads, config.n_groups, head_dim
                )
                V_mod = V_mod.view(
                    1, bsz * kv_seq_len, config.n_kv_heads, config.n_groups, head_dim
                )
            else:
                Q_mod = Q_mod.view(1, bsz * q_len, n_heads, head_dim)
                K_mod = K_mod.view(1, bsz * kv_seq_len, n_heads, head_dim)
                V_mod = V_mod.view(1, bsz * kv_seq_len, n_heads, head_dim)

        out = xformers_attention(
            Q_mod,
            K_mod,
            V_mod,
            attn_bias = attn_bias,
            **xformers_kwargs,
        )

        if config.n_groups != 1 and not requires_grad:
            out = out.view(bsz, q_len, config.n_kv_heads, config.n_groups, head_dim)
            out = out.reshape(bsz, q_len, n_heads, head_dim)
        else:
            out = out.view(bsz, q_len, n_heads, head_dim)
        return out
    else:
        local_mask = context.attention_mask
        is_causal_local = False
        if context.seq_info is not None and local_mask is None:
            local_mask = build_sdpa_packed_attention_mask(
                context.seq_info,
                dtype = Q.dtype,
                device = Q.device,
                sliding_window = sliding_window,
            )
        else:
            q_len_local = Q.shape[-2]
            k_len_local = K.shape[-2]
            # ---- SDPA mask normalization for left padding / 2D masks ----
            if local_mask is not None and isinstance(local_mask, torch.Tensor):
                local_mask = local_mask.to(device = Q.device)

                if local_mask.dim() == 2:
                    # key padding keep mask: (bsz, k_len), 1/True = real token
                    if local_mask.dtype == torch.bool:
                        key_keep = local_mask
                    else:
                        # tokenizer attention_mask is typically int 0/1
                        key_keep = local_mask != 0

                    past_len = (
                        k_len_local - q_len_local
                    )  # works for prefill (0) and decode
                    q_pos = torch.arange(
                        past_len, past_len + q_len_local, device = Q.device
                    )
                    k_pos = torch.arange(k_len_local, device = Q.device)

                    causal_keep = (
                        k_pos[None, :] <= q_pos[:, None]
                    )  # True = allowed (SDPA)
                    if sliding_window is not None:
                        causal_keep &= k_pos[None, :] >= (
                            q_pos[:, None] - (sliding_window - 1)
                        )

                    # (bsz, 1, q_len, k_len) boolean keep mask
                    local_mask = (
                        causal_keep[None, None, :, :] & key_keep[:, None, None, :]
                    )

                elif local_mask.dim() == 3:
                    # (bsz, q_len, k_len) -> (bsz, 1, q_len, k_len)
                    local_mask = local_mask[:, None, :, :]

                elif local_mask.dim() == 4:
                    if local_mask.dtype != torch.bool:
                        # Use boolean keep masks for better SDPA stability.
                        local_mask = local_mask.eq(0)
                else:
                    raise ValueError(
                        f"Unsupported SDPA attention_mask rank: {local_mask.dim()}"
                    )

                # Avoid NaNs from fully-masked rows (common with left padding).
                if local_mask.dtype == torch.bool:
                    no_allowed = ~local_mask.any(
                        dim = -1, keepdim = True
                    )  # (bsz,1,q_len,1)
                    local_mask = local_mask | no_allowed

            is_causal_local = local_mask is None and q_len_local == k_len_local

        kwargs = dict(sdpa_kwargs)
        kwargs.setdefault("attn_mask", local_mask)
        kwargs.setdefault("is_causal", is_causal_local)

        use_sdpa_gqa = SDPA_HAS_GQA and config.n_groups != 1
        if (
            use_sdpa_gqa
            and (not requires_grad)
            and isinstance(local_mask, torch.Tensor)
            and local_mask.dim() >= 3
            and local_mask.shape[0] > 1
        ):
            # Batched masked inference has shown row-coupled drift with SDPA GQA.
            # Fall back to explicit KV expansion for deterministic row-wise behavior.
            use_sdpa_gqa = False

        if use_sdpa_gqa:
            kwargs.setdefault("enable_gqa", True)
            out = scaled_dot_product_attention(Q, K, V, **kwargs)
            return out.transpose(1, 2)

        K_mod = K
        V_mod = V
        if config.n_groups != 1:
            K_mod = K[:, :, None, :, :].expand(
                bsz, config.n_kv_heads, config.n_groups, kv_seq_len, head_dim
            )
            V_mod = V[:, :, None, :, :].expand(
                bsz, config.n_kv_heads, config.n_groups, kv_seq_len, head_dim
            )
            K_mod = K_mod.reshape(bsz, n_heads, kv_seq_len, head_dim)
            V_mod = V_mod.reshape(bsz, n_heads, kv_seq_len, head_dim)

        out = scaled_dot_product_attention(
            Q.contiguous(),
            K_mod.contiguous(),
            V_mod.contiguous(),
            **kwargs,
        )
        return out.transpose(1, 2).contiguous()