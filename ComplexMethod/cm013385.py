def _numpy_empty_ellipsis_patch(index, tensor_ndim):
    """
    Patch for NumPy-compatible ellipsis behavior when ellipsis doesn't match any dimensions.

    In NumPy, when an ellipsis (...) doesn't actually match any dimensions of the input array,
    it still acts as a separator between advanced indices. PyTorch doesn't have this behavior.

    This function detects when we have:
    1. Advanced indexing on both sides of an ellipsis
    2. The ellipsis doesn't actually match any dimensions
    """
    if not isinstance(index, tuple):
        index = (index,)

    # Find ellipsis position
    ellipsis_pos = None
    for i, idx in enumerate(index):
        if idx is Ellipsis:
            ellipsis_pos = i
            break

    # If no ellipsis, no patch needed
    if ellipsis_pos is None:
        return index, lambda x: x, lambda x: x

    # Count non-ellipsis dimensions consumed by the index
    consumed_dims = 0
    for idx in index:
        is_bool, depth = _get_bool_depth(idx)
        if is_bool:
            consumed_dims += depth
        elif idx is Ellipsis or idx is None:
            continue
        else:
            consumed_dims += 1

    # Calculate how many dimensions the ellipsis should match
    ellipsis_dims = tensor_ndim - consumed_dims

    # Check if ellipsis doesn't match any dimensions
    if ellipsis_dims == 0:
        # Check if we have advanced indexing on both sides of ellipsis
        left_advanced = _has_advanced_indexing(index[:ellipsis_pos])
        right_advanced = _has_advanced_indexing(index[ellipsis_pos + 1 :])

        if left_advanced and right_advanced:
            # This is the case where NumPy and PyTorch differ
            # We need to ensure the advanced indices are treated as separated
            new_index = index[:ellipsis_pos] + (None,) + index[ellipsis_pos + 1 :]
            end_ndims = 1 + sum(
                1 for idx in index[ellipsis_pos + 1 :] if isinstance(idx, slice)
            )

            def squeeze_fn(x):
                return x.squeeze(-end_ndims)

            def unsqueeze_fn(x):
                if isinstance(x, torch.Tensor) and x.ndim >= end_ndims:
                    return x.unsqueeze(-end_ndims)
                return x

            return new_index, squeeze_fn, unsqueeze_fn

    return index, lambda x: x, lambda x: x