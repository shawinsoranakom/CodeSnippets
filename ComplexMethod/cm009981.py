def _match_levels(
    tensor: torch.Tensor,
    from_levels: list[DimEntry],
    to_levels: list[DimEntry],
    drop_levels: bool = False,
) -> torch.Tensor:
    """
    Reshape a tensor to match target levels using as_strided.

    Args:
        tensor: Input tensor to reshape
        from_levels: Current levels of the tensor
        to_levels: Target levels to match
        drop_levels: If True, missing dimensions are assumed to have stride 0

    Returns:
        Reshaped tensor
    """
    if from_levels == to_levels:
        return tensor

    sizes = tensor.size()
    strides = tensor.stride()

    if not drop_levels:
        if len(from_levels) > len(to_levels):
            raise AssertionError("Cannot expand dimensions without drop_levels")

    new_sizes = []
    new_strides = []

    for level in to_levels:
        # Find index of this level in from_levels
        try:
            idx = from_levels.index(level)
        except ValueError:
            # Level not found in from_levels
            if level.is_positional():
                new_sizes.append(1)
            else:
                new_sizes.append(level.dim().size)
            new_strides.append(0)
        else:
            new_sizes.append(sizes[idx])
            new_strides.append(strides[idx])

    return tensor.as_strided(new_sizes, new_strides, tensor.storage_offset())