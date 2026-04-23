def varlen_attn_out(
    out: torch.Tensor,
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    cu_seq_q: torch.Tensor,
    cu_seq_k: torch.Tensor | None,
    max_q: int,
    max_k: int,
    *,
    return_aux: AuxRequest | None = None,
    scale: float | None = None,
    window_size: tuple[int, int] = (-1, -1),
    enable_gqa: bool = False,
    seqused_k: torch.Tensor | None = None,
    block_table: torch.Tensor | None = None,
    num_splits: int | None = None,
) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
    r"""Compute variable-length attention using Flash Attention with a pre-allocated output tensor.

    Same as :func:`varlen_attn` but writes the attention output into the provided ``out`` tensor
    instead of allocating a new one.

    """
    num_heads_q = query.size(1)
    num_heads_k = key.size(2) if block_table is not None else key.size(1)
    if not enable_gqa and num_heads_q != num_heads_k:
        raise ValueError(
            f"Expect query and key/value to have the same number of heads "
            f"but got Hq={num_heads_q} and Hkv={num_heads_k}. "
            f"Try setting enable_gqa=True for GQA."
        )
    if enable_gqa and num_heads_q % num_heads_k != 0:
        raise ValueError(
            f"Expect number of query heads to be a multiple of kv heads for GQA "
            f"but got Hq={num_heads_q} and Hkv={num_heads_k}."
        )

    is_causal = window_size == (-1, 0)
    lse = torch.ops.torch_attn._varlen_attn_out(
        out,
        query,
        key,
        value,
        cu_seq_q,
        cu_seq_k,
        max_q,
        max_k,
        is_causal,
        scale,
        list(window_size),
        enable_gqa,
        seqused_k,
        block_table,
        num_splits,
    )
    if return_aux is not None and return_aux.lse:
        return out, lse
    return out