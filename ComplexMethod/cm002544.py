def _can_skip_causal_mask_xpu(
    padding_mask: torch.Tensor | None,
    query_length: int,
    kv_length: int,
    local_attention_size: int | None,
) -> bool:
    """
    XPU-specific logic for determining if we can skip causal mask creation.

    For XPU devices, we have special handling:
    - Single query tokens (query_length == 1) use the same logic as CUDA
    - Multi-query tokens can skip if padding_mask is provided and correctly structured
      The mask must have all True values in the query window and all False after
    """

    if is_tracing(padding_mask):
        return False

    # Check local attention constraint (same as CUDA)
    if local_attention_size is not None and kv_length >= local_attention_size:
        return False

    if padding_mask is None:
        # Without padding mask, can skip if single query token or full causal attention
        return query_length == 1 or kv_length == query_length

    # XPU allows skipping under additional conditions when padding_mask is provided
    if query_length == 1:
        # Single query token: skip only if no padding tokens present
        return padding_mask.all()

    # XPU-specific: check if query window is all True and rest is all False
    # This allows XPU to optimize the 1st token in static cache
    return padding_mask[:, :query_length].all() and not padding_mask[:, query_length:].any()