def _compute_non_contiguous_dense_strides(size: tuple[int, ...]) -> list[int]:
    """
    Helper function to compute non-contiguous but dense strides (e.g., column-major order).

    Args:
        size: Tensor shape/size as a tuple of integers

    Returns:
        list[int]: List of non-contiguous dense strides
    """
    if len(size) <= 1:
        # For 0D or 1D tensors, return same as contiguous
        return _compute_contiguous_strides(size)

    # Generate different dense patterns
    patterns = [
        "column_major",  # Reverse order (left to right instead of right to left)
        "random_permute",  # Random permutation of dimensions
        "middle_out",  # Start from middle dimension
    ]

    pattern: str = random.choice(patterns)

    if pattern == "column_major":
        # Column-major order: calculate strides from left to right
        strides: list[int] = [0] * len(size)
        current_stride: int = 1

        # Calculate strides from left to right (opposite of contiguous)
        for i in range(len(size)):
            strides[i] = current_stride
            # For dimensions with size 0, keep stride as is
            if size[i] != 0:
                current_stride *= size[i]

        return strides

    elif pattern == "random_permute":
        # Create a valid permutation that's still dense
        # Create dimension permutation
        indices = list(range(len(size)))
        random.shuffle(indices)

        # Apply permutation to get new dense layout
        new_strides = [0] * len(size)
        current_stride = 1

        # Sort indices by their corresponding size to maintain density
        sorted_indices = sorted(
            indices, key=lambda i: size[i] if size[i] != 0 else float("inf")
        )

        for idx in sorted_indices:
            new_strides[idx] = current_stride
            if size[idx] != 0:
                current_stride *= size[idx]

        return new_strides

    elif pattern == "middle_out":
        # Start from middle dimension and work outward
        strides = [0] * len(size)
        current_stride = 1

        # Start from middle
        middle = len(size) // 2
        processed = [False] * len(size)

        # Process middle first
        strides[middle] = current_stride
        if size[middle] != 0:
            current_stride *= size[middle]
        processed[middle] = True

        # Process alternating left and right
        for offset in range(1, len(size)):
            for direction in [-1, 1]:
                idx = middle + direction * offset
                if 0 <= idx < len(size) and not processed[idx]:
                    strides[idx] = current_stride
                    if size[idx] != 0:
                        current_stride *= size[idx]
                    processed[idx] = True
                    break

        return strides

    # Fallback to contiguous
    return _compute_contiguous_strides(size)