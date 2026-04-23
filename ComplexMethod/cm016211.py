def fuzz_valid_stride(size: tuple[int, ...]) -> tuple[int, ...]:
    """
    Fuzzes PyTorch tensor strides by generating valid stride patterns for a given size.

    Args:
        size: Tensor shape/size as a tuple of integers

    Returns:
        Tuple[int, ...]: A tuple representing valid tensor strides
    """

    if len(size) == 0:
        # Scalar tensor has no strides
        return ()

    # Choose stride pattern type
    stride_types = [
        "contiguous",  # Normal contiguous memory layout
        "transposed",  # Transposed dimensions
        "custom_gaps",  # Custom strides with gaps (non-dense)
        "minimal",  # Minimal valid strides (all ones)
        "nonoverlapping_and_dense",  # Non-overlapping and dense (contiguous)
        "nonoverlapping_and_dense_non_contig",  # Non-overlapping and dense but not contiguous
        "overlapping",  # Overlapping memory access (zero strides)
        "sparse_gaps",  # Large gaps (definitely non-dense)
    ]

    stride_type: str = random.choice(stride_types)

    if stride_type in ["contiguous", "nonoverlapping_and_dense"]:
        # Standard contiguous strides: stride[i] = product of sizes[i+1:]
        return tuple(_compute_contiguous_strides(size))

    elif stride_type == "transposed":
        # Create transposed version - swap some dimensions' strides
        base_strides = list(_compute_contiguous_strides(size))

        if len(base_strides) >= 2:
            # Randomly swap strides of two dimensions
            i, j = random.sample(range(len(base_strides)), 2)
            base_strides[i], base_strides[j] = base_strides[j], base_strides[i]

        return tuple(base_strides)

    elif stride_type == "custom_gaps":
        # Create strides with custom gaps/spacing
        base_strides = list(_compute_contiguous_strides(size))

        # Add random gaps to some strides
        for i in range(len(base_strides)):
            if size[i] != 0 and random.random() < 0.3:  # 30% chance to add gap
                gap_multiplier: int = random.randint(2, 5)
                base_strides[i] *= gap_multiplier

        return tuple(base_strides)

    elif stride_type == "minimal":
        # Minimal valid strides (all ones)
        return tuple([1] * len(size))

    elif stride_type == "nonoverlapping_and_dense_non_contig":
        # Non-overlapping and dense but not contiguous (e.g., column-major)
        return tuple(_compute_non_contiguous_dense_strides(size))

    elif stride_type == "overlapping":
        # Create overlapping strides (zero strides for some dimensions)
        base_strides = list(_compute_contiguous_strides(size))

        # Randomly set some strides to 0 to cause overlapping
        for i in range(len(base_strides)):
            if size[i] > 1 and random.random() < 0.4:  # 40% chance to make overlapping
                base_strides[i] = 0

        return tuple(base_strides)

    elif stride_type == "sparse_gaps":
        # Create strides with very large gaps (definitely non-dense)
        base_strides = list(_compute_contiguous_strides(size))

        # Add very large gaps to create sparse layout
        for i in range(len(base_strides)):
            if size[i] > 1:
                gap_multiplier: int = random.randint(10, 100)  # Much larger gaps
                base_strides[i] *= gap_multiplier

        return tuple(base_strides)

    # Fallback to contiguous
    return tuple(_compute_contiguous_strides(size))