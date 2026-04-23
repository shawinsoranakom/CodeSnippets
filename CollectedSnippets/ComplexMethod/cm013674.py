def varlen_attn(
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
    r"""Compute variable-length attention using Flash Attention.

    This function is similar to scaled_dot_product_attention but optimized for
    variable-length sequences using cumulative sequence position tensors.

    Args:
        query (Tensor): Query tensor; shape :math:`(T_q, H_q, D)`
        key (Tensor): Key tensor; shape :math:`(T_k, H_{kv}, D)`, or
            :math:`(\text{total\_pages}, \text{page\_size}, H_{kv}, D)` when ``block_table`` is provided.
        value (Tensor): Value tensor; shape :math:`(T_k, H_{kv}, D)`, or
            :math:`(\text{total\_pages}, \text{page\_size}, H_{kv}, D)` when ``block_table`` is provided.
        cu_seq_q (Tensor): Cumulative sequence positions for queries; shape :math:`(N+1,)`
        cu_seq_k (Tensor): Cumulative sequence positions for keys/values; shape :math:`(N+1,)`
        max_q (int): Maximum query sequence length in the batch.
        max_k (int): Maximum key/value sequence length in the batch.
        return_aux (Optional[AuxRequest]): If not None and ``return_aux.lse`` is True, also returns the logsumexp tensor.
        scale (float, optional): Scaling factor for attention scores
        window_size (tuple[int, int], optional): Window size for sliding window attention as (left, right).
            Use (-1, -1) for full attention (default), (-1, 0) for causal attention,
            or (W, 0) for causal attention with sliding window of size W.
        enable_gqa (bool): If set to True, enables Grouped Query Attention (GQA)
            and allows key/value to have fewer heads than query.
            Each KV head is shared by a group of :math:`H_q / H_{kv}` query heads,
            so :math:`H_q` must be divisible by :math:`H_{kv}`.
            Default is False.
        seqused_k (Tensor, optional): Number of valid KV tokens per batch element; shape :math:`(N,)`.
            When set, only the first ``seqused_k[i]`` tokens in the key/value sequence for batch
            element *i* participate in attention. Useful for KV-cache decoding where the cache slot
            is larger than the actual sequence. Inference-only (not supported in backward).
        block_table (Tensor, optional): Block table for paged KV cache; shape
            :math:`(N, \text{max\_pages\_per\_seq})`, dtype ``int32``.
            Requires ``seqused_k``. Inference-only (not supported in backward).

            When ``block_table`` is provided, ``key`` and ``value`` are a "pool" of
            pages of tokens of KV data and the pages belong to any sequence/order.
            The ``block_table`` is what maps each sequence's logical chunks
            back to physical pages in this pool.

            ``seqused_k[i]`` tells the kernel how many tokens in sequence *i* are
            actually valid, since the last page is typically only partially filled.
        num_splits (int, optional): Number of splits for split-KV. Set to ``1``
            to disable split-KV which enables batch invariance. Split-KV
            parallelizes the key/value sequence dimension across multiple thread
            blocks and combines partial results. The split decision depends
            on ``max_k`` (the longest sequence in the batch), so different batch
            compositions can change the reduction order and produce different
            floating-point results for the same sequence. When this is disabled,
            bitwise identical outputs are guaranteed for a given sequence
            regardless of what other sequences are in the batch, at the
            cost of lower GPU utilization when there are few queries. When
            ``None`` (default), the kernel chooses automatically.

    Returns:
        output (Tensor): Output tensor from attention computation; shape :math:`(T_q, H_q, D)`.

        If ``return_aux`` is not None and ``return_aux.lse`` is True:
            lse (Tensor): Log-sum-exp of attention scores; shape :math:`(T_q, H_q)`.

    Shape legend:
        - :math:`N`: Batch size
        - :math:`T_q`: Total number of query tokens in the batch (sum of all query sequence lengths)
        - :math:`T_k`: Total number of key/value tokens in the batch (sum of all key/value sequence lengths)
        - :math:`H_q`: Number of query attention heads
        - :math:`H_{kv}`: Number of key/value attention heads (equal to :math:`H_q` unless GQA is enabled)
        - :math:`D`: Head dimension

    Example::

        >>> # xdoctest: +REQUIRES(env:TORCH_DOCTEST_CUDA)
        >>> batch_size, max_seq_len, embed_dim, num_heads = 2, 512, 1024, 16
        >>> head_dim = embed_dim // num_heads
        >>> seq_lengths = []
        >>> for _ in range(batch_size):
        ...     length = torch.randint(1, max_seq_len // 64 + 1, (1,)).item() * 64
        ...     seq_lengths.append(min(length, max_seq_len))
        >>> seq_lengths = torch.tensor(seq_lengths, device="cuda")
        >>> total_tokens = seq_lengths.sum().item()
        >>>
        >>> # Create packed query, key, value tensors
        >>> query = torch.randn(
        ...     total_tokens, num_heads, head_dim, dtype=torch.float16, device="cuda"
        ... )
        >>> key = torch.randn(
        ...     total_tokens, num_heads, head_dim, dtype=torch.float16, device="cuda"
        ... )
        >>> value = torch.randn(
        ...     total_tokens, num_heads, head_dim, dtype=torch.float16, device="cuda"
        ... )
        >>>
        >>> # Build cumulative sequence tensor
        >>> cu_seq = torch.zeros(batch_size + 1, device="cuda", dtype=torch.int32)
        >>> cu_seq[1:] = seq_lengths.cumsum(0)
        >>> max_len = seq_lengths.max().item()
        >>>
        >>> # Call varlen_attn
        >>> output = varlen_attn(
        ...     query, key, value, cu_seq, cu_seq, max_len, max_len
        ... )
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
    out, lse, _ = torch.ops.torch_attn._varlen_attn(
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