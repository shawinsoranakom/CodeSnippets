def _numpy_compatible_indexing(index):
    """Convert scalar indices to lists when advanced indexing is present for NumPy compatibility."""
    if not isinstance(index, tuple):
        index = (index,)

    # Check if there's any advanced indexing (sequences, booleans, or tensors)
    has_advanced = _has_advanced_indexing(index)

    if not has_advanced:
        return index

    # Convert integer scalar indices to single-element lists when advanced indexing is present
    # Note: Do NOT convert boolean scalars (True/False) as they have special meaning in NumPy
    converted = []
    for idx in index:
        if isinstance(idx, int) and not isinstance(idx, bool):
            # Integer scalars should be converted to lists
            converted.append([idx])
        elif (
            isinstance(idx, torch.Tensor)
            and idx.ndim == 0
            and not torch.is_floating_point(idx)
            and idx.dtype != torch.bool
        ):
            # Zero-dimensional tensors holding integers should be treated the same as integer scalars
            converted.append([idx])
        else:
            # Everything else (booleans, lists, slices, etc.) stays as is
            converted.append(idx)

    return tuple(converted)