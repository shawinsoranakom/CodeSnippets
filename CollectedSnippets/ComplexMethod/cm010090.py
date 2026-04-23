def meta__scaled_dot_product_flash_attention(
    query: Tensor,
    key: Tensor,
    value: Tensor,
    dropout_p: float = 0.0,
    is_causal: bool = False,
    return_debug_mask: bool = False,
    scale: float | None = None,
):
    batch_size = query.size(0)
    num_heads = query.size(1)
    max_seqlen_batch_q = query.size(2)
    head_dim = query.size(3)
    max_seqlen_batch_k = key.size(2)

    attention = torch.empty_like(query)
    logsumexp = torch.empty(
        (batch_size, num_heads, max_seqlen_batch_q),
        dtype=torch.float,
        device=query.device,
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

    # Note [Seed and Offset]: device for seed and offset below depends on whether we are
    # capturing or not, but at the time of tracing we don't know if we
    # are going to use cudagraphs or not, so we return meta tensors here
    # it's possible we'll need to have some special handling in inductor for sdpa
    # See [Note] BC breaking change to flash seed/offset
    if torch.version.hip and torch.cuda.is_available() or device_hint(query) == "xpu":
        # Maintain old path on AMD
        seed = torch.empty((), dtype=torch.long, device="meta")
        offset = torch.empty((), dtype=torch.long, device="meta")
    else:
        seed = torch.empty((2), dtype=torch.uint64, device="meta")
        offset = torch.empty((), dtype=torch.uint64, device="meta")

    return (
        attention,
        logsumexp,
        None,
        None,
        max_seqlen_batch_q,
        max_seqlen_batch_k,
        seed,
        offset,
        debug_mask,
    )