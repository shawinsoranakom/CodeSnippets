def _calculate_max_contiguous_elements(
    indices: list[int],
    sub_tensor_shape: list[int],
    tensor_shape: list[int],
) -> int:
    """
    Calculate the maximum number of contiguous elements that can be written from current position.

    This determines the largest chunk by checking how elements are laid out in memory
    and finding natural boundaries where contiguity breaks.

    Args:
        indices: Current position indices in the sub-tensor
        sub_tensor_shape: Shape of the sub-tensor being written
        tensor_shape: Shape of the full tensor

    Raises:
        ValueError: If input lists are empty, have mismatched lengths, or contain invalid values
    """
    # Validate input lists are not empty
    if not indices or not sub_tensor_shape or not tensor_shape:
        raise ValueError("Input lists cannot be empty")

    # Validate all lists have the same length (same number of dimensions)
    if not (len(indices) == len(sub_tensor_shape) == len(tensor_shape)):
        raise ValueError(
            f"All input lists must have the same length. Got indices: {len(indices)}, "
            f"sub_tensor_shape: {len(sub_tensor_shape)}, tensor_shape: {len(tensor_shape)}"
        )

    # Validate indices are within bounds of sub_tensor_shape
    for i, (idx, sub_dim) in enumerate(zip(indices, sub_tensor_shape)):
        if idx >= sub_dim:
            raise ValueError(
                f"Index {idx} at dimension {i} is out of bounds for sub-tensor shape {sub_tensor_shape}"
            )

    # Validate sub_tensor dimensions don't exceed tensor dimensions
    for i, (sub_dim, tensor_dim) in enumerate(zip(sub_tensor_shape, tensor_shape)):
        if sub_dim > tensor_dim:
            raise ValueError(
                f"Sub-tensor dimension {sub_dim} at position {i} exceeds tensor dimension {tensor_dim}"
            )

    # Start with elements remaining in the last dimension
    max_contiguous = sub_tensor_shape[-1] - indices[-1]

    # Check if we can extend across multiple dimensions
    # We can write across dimension boundaries if we're writing complete "rows"
    # and the layout in destination tensor maintains contiguity

    # For 2D case: check if we can write multiple complete rows
    if len(sub_tensor_shape) >= 2:
        # If we're at the start of a row and can write complete rows
        if indices[-1] == 0:  # At start of last dimension (column)
            rows_remaining = sub_tensor_shape[-2] - indices[-2]  # Rows left to write

            # Check if writing complete rows maintains contiguity in destination
            # This is true for row-wise sharding or when sub-tensor spans full width
            if sub_tensor_shape[-1] == tensor_shape[-1]:  # Full width
                max_contiguous = rows_remaining * sub_tensor_shape[-1]

            # For higher dimensions, check if we can extend further
            if len(sub_tensor_shape) >= 3 and indices[-2] == 0:
                # Check if we can write complete 2D slices
                remaining_in_dim = sub_tensor_shape[-3] - indices[-3]
                if (
                    sub_tensor_shape[-1] == tensor_shape[-1]
                    and sub_tensor_shape[-2] == tensor_shape[-2]
                ):
                    max_contiguous = (
                        remaining_in_dim * sub_tensor_shape[-2] * sub_tensor_shape[-1]
                    )

    return max_contiguous