def _validate_descale(
    descale: Tensor | None,
    name: str,
    query: Tensor,
    key: Tensor,
    descale_type: DescaleType,
) -> None:
    """Validate descale tensor for the specified scaling type.

    Args:
        descale: The descale tensor to validate (may be None)
        name: Name of the descale tensor ("q", "k", or "v") for error messages
        query: Query tensor to get batch size
        key: Key tensor to get num_kv_heads
        descale_type: The scaling granularity being used

    Raises:
        ValueError: If the descale tensor has invalid dtype, device, or shape

    Note:
        All descale tensors (q, k, v) use num_kv_heads for the head dimension.
        For GQA/MQA where num_query_heads > num_kv_heads, q_descale is broadcast
        from (B, H_kv) to match the query heads internally.
    """
    if descale is None:
        return

    # Check dtype
    if descale.dtype != torch.float32:
        raise ValueError(f"{name}_descale must have dtype float32, got {descale.dtype}")

    # Check device
    if not descale.is_cuda:
        raise ValueError(f"{name}_descale must be a CUDA tensor")

    # Check shape based on descale type
    if descale_type == DescaleType.PER_HEAD:
        batch_size = query.size(0)
        # All descale tensors use num_kv_heads, even q_descale (broadcast internally)
        # For BHSD layout, num_kv_heads is at dim 1 of key
        num_kv_heads = key.size(1)

        if descale.dim() != 2:
            raise ValueError(
                f"{name}_descale must be a 2D tensor with shape (batch_size, num_kv_heads) "
                f"for PER_HEAD descaling, got {descale.dim()}D tensor"
            )

        if descale.size(0) != batch_size:
            raise ValueError(
                f"{name}_descale batch dimension must match query batch size, "
                f"expected {batch_size}, got {descale.size(0)}"
            )

        if descale.size(1) != num_kv_heads:
            raise ValueError(
                f"{name}_descale head dimension must match num_kv_heads, "
                f"expected {num_kv_heads}, got {descale.size(1)}"
            )