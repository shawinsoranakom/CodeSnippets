def flash_attn_varlen_func(
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        cu_seqlens_q: torch.Tensor,
        max_seqlen_q: int,
        max_seqlen_k: int,
        softmax_scale: float | None = None,
        causal: bool = False,
        out: torch.Tensor | None = None,
        block_table: torch.Tensor | None = None,
        alibi_slopes: torch.Tensor | None = None,
        window_size: list[int] | None = None,
        softcap: float | None = 0.0,
        seqused_k: torch.Tensor | None = None,
        cu_seqlens_k: torch.Tensor | None = None,
        # passed in qwen vl
        dropout_p: float = 0.0,
        # The following parameters are not used in xpu kernel currently,
        # we keep API compatible to CUDA's.
        scheduler_metadata=None,
        fa_version: int = 2,
        q_descale=None,
        k_descale=None,
        v_descale=None,
        num_splits=0,
        return_softmax_lse: bool | None = False,
        s_aux: torch.Tensor | None = None,
        return_attn_probs: bool | None = False,
    ):
        assert cu_seqlens_k is not None or seqused_k is not None, (
            "cu_seqlens_k or seqused_k must be provided"
        )
        assert cu_seqlens_k is None or seqused_k is None, (
            "cu_seqlens_k and seqused_k cannot be provided at the same time"
        )
        assert block_table is None or seqused_k is not None, (
            "when enable block_table, seqused_k is needed"
        )
        assert block_table is not None or cu_seqlens_k is not None, (
            "when block_table is disabled, cu_seqlens_k is needed"
        )
        if out is None:
            out = torch.empty(q.shape, dtype=q.dtype, device=q.device)
        real_window_size: tuple[int, int]
        if window_size is None:
            real_window_size = (-1, -1)
        else:
            assert len(window_size) == 2
            real_window_size = (window_size[0], window_size[1])  # noqa: F841

        # In encode attention, k and v maybe not contiguous and current
        # kernel can't handle it
        if block_table is None:
            k = k.contiguous()
            v = v.contiguous()
        return flash_attn_varlen_func(
            out=out,
            q=q.contiguous(),
            k=k,
            v=v,
            cu_seqlens_q=cu_seqlens_q,
            cu_seqlens_k=cu_seqlens_k,
            seqused_k=seqused_k,
            max_seqlen_q=max_seqlen_q,
            max_seqlen_k=max_seqlen_k,
            softmax_scale=softmax_scale,
            causal=causal,
            block_table=block_table,
            s_aux=s_aux,
            window_size=real_window_size,
            # alibi_slopes = alibi_slopes,
            # softcap=softcap,
            return_softmax_lse=return_softmax_lse,
            q_descale=q_descale,
            k_descale=k_descale,
            v_descale=v_descale,
        )