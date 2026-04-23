def meta__flash_attention_forward(
    query: Tensor,
    key: Tensor,
    value: Tensor,
    cum_seq_q: Tensor | None,
    cum_seq_k: Tensor | None,
    max_q: int,
    max_k: int,
    dropout_p: float,
    is_causal: bool,
    return_debug_mask: bool,
    scale: float | None = None,
    window_size_left: int | None = None,
    window_size_right: int | None = None,
    seqused_k: Tensor | None = None,
    alibi_slopes: Tensor | None = None,
    block_table: Tensor | None = None,
    num_splits: int | None = None,
):
    # NB: there are two underlying paths:
    # 1. normal dense path; expect 4D inputs of shape (batch_size, seqlen, num_heads, head_dim)
    # 2. varseqlen path; expect 3D inputs of shape (total, num_heads, head_dim) where total
    #    includes all batch item sequences. cum_seq_q / cum_seq_k contain offsets into total
    batch_size = query.size(0) if cum_seq_q is None else cum_seq_q.numel() - 1
    max_seqlen_batch_q = query.size(1) if cum_seq_q is None else max_q
    max_seqlen_batch_k = key.size(1) if cum_seq_k is None else max_k
    num_heads = query.size(-2)
    head_dim = query.size(-1)

    # Cuda Path
    attention = torch.empty_like(query)
    if cum_seq_q is None:
        logsumexp = torch.empty(
            (batch_size, num_heads, max_seqlen_batch_q),
            dtype=torch.float,
            device=query.device,
        )
    else:
        total_q = query.size(0)
        logsumexp = torch.empty(
            (num_heads, total_q), dtype=torch.float, device=query.device
        )

    if return_debug_mask:
        blocksize_c = 128 if head_dim > 64 else 256
        max_seqlen_k = math.ceil(max_seqlen_batch_q / blocksize_c)
        if max_seqlen_batch_k <= 128:
            max_seqlen_k = 128
        elif max_seqlen_batch_k <= 256:
            max_seqlen_k = 256
        debug_mask = torch.empty(
            (batch_size, num_heads, max_seqlen_batch_q, max_seqlen_k),
            dtype=query.dtype,
            device=query.device,
        )
    else:
        debug_mask = torch.empty(0, dtype=query.dtype, device=query.device)

    # See Note [Seed and Offset]
    # See [Note] BC breaking change to flash seed/offset
    seed, offset = None, None
    if torch.version.hip and torch.cuda.is_available():
        # Maintain old path on AMD
        seed = torch.empty((), dtype=torch.long, device="meta")
        offset = torch.empty((), dtype=torch.long, device="meta")
    else:
        seed = torch.empty((2), dtype=torch.uint64, device="meta")
        offset = torch.empty((), dtype=torch.uint64, device="meta")
    return (
        attention,
        logsumexp,
        seed,
        offset,
        debug_mask,
    )