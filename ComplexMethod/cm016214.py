def fuzz_scalar(spec, seed: int | None = None) -> float | int | bool | complex:
    """
    Create a Python scalar value from a ScalarSpec.

    Args:
        spec: ScalarSpec containing the desired dtype and optionally a constant value
        seed: Random seed for reproducibility. If None, uses current random state.

    Returns:
        Python scalar (float, int, bool, complex) matching the dtype
    """
    # If a constant value is specified, use it directly
    if spec.constant is not None:
        return spec.constant

    # Create a local random instance to avoid interfering with global state
    if seed is not None:
        local_random = random.Random(seed)
        # Save and restore global random state
        old_random_state = random.getstate()
        try:
            random.setstate(local_random.getstate())

            # Create a scalar value based on dtype
            if spec.dtype.is_floating_point:
                return random.uniform(-10.0, 10.0)
            elif spec.dtype in [torch.complex64, torch.complex128]:
                # Only generate complex values if not avoiding complex dtypes
                if FuzzerConfig.avoid_complex:
                    raise ValueError(
                        "Cannot generate complex values with avoid_complex=True"
                    )
                return complex(random.uniform(-10.0, 10.0), random.uniform(-10.0, 10.0))
            else:  # integer or bool
                if spec.dtype == torch.bool:
                    return random.choice([True, False])
                else:
                    return random.randint(-10, 10)
        finally:
            # Restore original random state
            random.setstate(old_random_state)
    else:
        # Use current random state when no seed provided
        # Create a scalar value based on dtype
        if spec.dtype.is_floating_point:
            return random.uniform(-10.0, 10.0)
        elif spec.dtype in [torch.complex64, torch.complex128]:
            # Only generate complex values if not avoiding complex dtypes
            if FuzzerConfig.avoid_complex:
                raise ValueError(
                    "Cannot generate complex values with avoid_complex=True"
                )
            return complex(random.uniform(-10.0, 10.0), random.uniform(-10.0, 10.0))
        else:  # integer or bool
            if spec.dtype == torch.bool:
                return random.choice([True, False])
            else:
                return random.randint(-10, 10)