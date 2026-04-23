def fuzz_tensor(
    size: tuple[int, ...] | None = None,
    stride: tuple[int, ...] | None = None,
    dtype: torch.dtype | None = None,
    seed: int | None = None,
) -> tuple[torch.Tensor, int]:
    """
    Create a tensor with fuzzed size, stride, and dtype.

    Args:
        size: Tensor shape. If None, will be randomly generated.
        stride: Tensor stride. If None, will be randomly generated based on size.
        dtype: Tensor data type. If None, will be randomly generated.
        seed: Random seed for reproducibility. If None, will be randomly generated.

    Returns:
        Tuple[torch.Tensor, int]: A tuple of (tensor, seed_used) where tensor has
        the specified or randomly generated properties, and seed_used is the seed
        that was used for generation (for reproducibility).
    """
    # Generate or use provided seed
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    # Create a local Random instance to avoid interfering with global state
    local_random = random.Random(seed)

    # Set the torch random seed for reproducibility
    # Save and restore global torch state to avoid side effects
    torch_state = torch.get_rng_state()
    torch.manual_seed(seed)

    # Generate random values if not provided using local random instance
    old_random_state = random.getstate()
    try:
        # Temporarily use local random instance for deterministic generation
        random.setstate(local_random.getstate())

        if size is None:
            size = fuzz_tensor_size()

        if dtype is None:
            dtype = fuzz_torch_tensor_type("default")

        if stride is None:
            stride = fuzz_valid_stride(size)

        # Handle empty tensor case
        if len(size) == 0:
            return torch.ones((), dtype=dtype), seed

        # Calculate required storage size for the custom stride
        required_storage = _compute_storage_size_needed(size, stride)

        # Create base tensor with sufficient storage
        if FuzzerConfig.use_real_values:
            # Use random values based on dtype
            if dtype.is_floating_point:
                base_tensor = torch.randn(required_storage, dtype=dtype)
            elif dtype in [torch.complex64, torch.complex128]:
                # Create complex tensor with random real and imaginary parts
                real_part = torch.randn(
                    required_storage,
                    dtype=torch.float32 if dtype == torch.complex64 else torch.float64,
                )
                imag_part = torch.randn(
                    required_storage,
                    dtype=torch.float32 if dtype == torch.complex64 else torch.float64,
                )
                base_tensor = torch.complex(real_part, imag_part).to(dtype)
            elif dtype == torch.bool:
                base_tensor = torch.randint(0, 2, (required_storage,), dtype=torch.bool)
            else:  # integer types
                base_tensor = torch.randint(-100, 100, (required_storage,), dtype=dtype)
        else:
            # Use zeros (default behavior)
            base_tensor = torch.ones(required_storage, dtype=dtype)

        # Create strided tensor view
        strided_tensor = torch.as_strided(base_tensor, size, stride)

        return strided_tensor, seed
    finally:
        # Restore original random state
        random.setstate(old_random_state)
        # Restore original torch state
        torch.set_rng_state(torch_state)