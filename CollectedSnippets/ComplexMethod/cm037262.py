def apply_top_k_top_p_triton(
    logits: torch.Tensor,
    k: torch.Tensor | None,
    p: torch.Tensor | None,
    mask_value: float = float("-inf"),
) -> torch.Tensor:
    """
    Apply combined top-k and top-p masking using Triton.

    Top-k is applied first (by logit value), then top-p is applied
    to the remaining k values (by probability).

    Args:
        logits: [batch_size, vocab_size] float32 tensor, modified in-place
        k: [batch_size] int32 tensor of top-k values per row, or None to disable top-k
        p: [batch_size] float32 tensor of top-p values per row (0 to 1),
            or None to disable top-p
        mask_value: Value for masked positions (default: -inf)

    Returns:
        The logits tensor (modified in-place)
    """
    assert logits.ndim == 2
    assert logits.dtype == torch.float32

    batch_size, vocab_size = logits.shape

    topk_enabled = k is not None
    topp_enabled = p is not None

    if batch_size == 0 or not (topk_enabled or topp_enabled):
        return logits

    if k is not None:
        assert k.ndim == 1 and k.shape[0] == batch_size
        k_ptr = k.to(torch.int32)
    else:
        k_ptr = logits  # Dummy pointer (won't be read)

    if p is not None:
        assert p.ndim == 1 and p.shape[0] == batch_size
        p_ptr = p.to(torch.float32)
    else:
        p_ptr = logits  # Dummy pointer (won't be read)

    num_sm = num_compute_units(logits.device.index)
    NUM_PROGRAMS = min(num_sm, batch_size)

    # Cache per-Triton Program buffer on each device.
    buf_key = (logits.device, logits.dtype, vocab_size)
    buffer = _TRITON_BUFFER_CACHE.get(buf_key)
    if buffer is None or buffer.shape[0] < NUM_PROGRAMS:
        size = min(next_power_of_2(NUM_PROGRAMS), num_sm)
        buffer = logits.new_empty((size, vocab_size))
        _TRITON_BUFFER_CACHE[buf_key] = buffer
    if buffer.shape[0] > NUM_PROGRAMS:
        buffer = buffer[:NUM_PROGRAMS]

    # Cache lookup table entries on each device.
    tables = _TRITON_TABLE_CACHE.get(logits.device)
    if tables is None:
        normal_cdf_to_sigma_table = logits.new_tensor(_NORMAL_CDF_TO_SIGMA_TABLE)
        percentile_to_std_table = logits.new_tensor(_PERCENTILE_TO_STD_TABLE)
        _TRITON_TABLE_CACHE[logits.device] = (
            normal_cdf_to_sigma_table,
            percentile_to_std_table,
        )
    else:
        normal_cdf_to_sigma_table, percentile_to_std_table = tables

    _topk_topp_kernel[(NUM_PROGRAMS,)](
        logits,
        buffer,
        percentile_to_std_table,
        normal_cdf_to_sigma_table,
        k_ptr,
        p_ptr,
        BATCH_SIZE=batch_size,
        MASK_VALUE=mask_value,
        VOCAB_SIZE=vocab_size,
        BLOCK_SIZE=8192,
        BLOCK_SIZE_TRUNC=4096,
        TOPK_ENABLED=topk_enabled,
        TOPP_ENABLED=topp_enabled,
    )

    return logits