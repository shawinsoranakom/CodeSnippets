def get_complete_tensor(
    group: OrderedSet[tuple[str, str]], models_weights: dict[str, Weights]
) -> torch.Tensor:
    """
    Given a group of (model_name, weight_name) pairs whose tensors share the same
    underlying storage, return the complete (maximal) tensor covering that storage
    region.

    This function handles two cases:

    1. If any tensor in the group is already marked as complete, return it directly.
    2. Otherwise, all tensors in the group are assumed to be slices of a larger,
        contiguous tensor backed by the same storage. In this case, reconstruct
        the complete tensor by taking the union of their storage ranges. This assumes
        all tensors in the group have the same dtype.

    Args:
        group: Set of (model_name, weight_name) tuples identifying tensors that share storage.
        models_weights: Dictionary mapping model names to their Weights objects.

    Returns:
        The complete tensor (either found directly or reconstructed from slices).

    Example:
        # Tensors a, b, c share storage:
        # a = full_tensor[0:5]   -> start=addr_0, end=addr_5
        # b = full_tensor[3:8]   -> start=addr_3, end=addr_8
        # c = full_tensor        -> complete tensor

        # Case 1: If c is in group -> return c
        # Case 2: If only a, b in group -> reconstruct from addr_0 to addr_8
    """

    if len(group) == 0:
        raise AssertionError("group cannot be empty")

    start_addr = None
    end_addr = None
    for model_name, weight_name in group:
        tensor_property = models_weights[model_name].get_weight_properties(weight_name)

        # Case 1: Found a complete tensor.
        if tensor_property.is_complete():
            return models_weights[model_name].get_weight(weight_name)[0]

        # Case 2: Track the widest boundary across all slices.
        if tensor_property.start is not None:
            start_addr = (
                tensor_property.start
                if start_addr is None
                else min(start_addr, tensor_property.start)
            )
        if tensor_property.end is not None:
            end_addr = (
                tensor_property.end
                if end_addr is None
                else max(end_addr, tensor_property.end)
            )

    # Case 2: Reconstruct complete tensor from slices.
    # Pick any tensor from the group as a reference (they all share the same storage).
    warnings.warn(
        "No complete tensor found in the group! Returning the first one. "
        "This may cause issues when your weights are not on CPU.",
        stacklevel=2,
    )

    model_name, weight_name = next(iter(group))
    reference_tensor = models_weights[model_name].get_weight(weight_name)[0]

    # If no boundary information available (e.g., FakeTensor), return reference tensor as is.
    if start_addr is None and end_addr is None:
        return reference_tensor

    # Validate that we have both boundaries.
    if start_addr is None or end_addr is None:
        raise AssertionError(
            f"Inconsistent boundary information: start={start_addr}, end={end_addr}. "
            "Unable to reconstruct complete tensor from group."
        )

    # Reconstruct a view over the full contiguous storage range.
    storage = reference_tensor.untyped_storage()
    total_size_bytes = end_addr - storage.data_ptr()
    element_size = reference_tensor.element_size()
    # It assumes all tensors in the group have the same dtype.
    total_size = total_size_bytes // element_size

    # Validate alignment: size must be multiples of element_size.
    if total_size_bytes % element_size != 0:
        raise AssertionError(
            f"Total size ({total_size_bytes} bytes) is not aligned with "
            f"element size ({element_size} bytes). Cannot reconstruct tensor safely. "
            f"Expected size to be a multiple of {element_size}."
        )

    # Reconstruct a tensor that spans the needed storage range, the metadata will be handled separately.
    return torch.tensor(
        [], device=reference_tensor.device, dtype=reference_tensor.dtype
    ).set_(
        storage,
        0,
        torch.Size([total_size]),
        (),
    )