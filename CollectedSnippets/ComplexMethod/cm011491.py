def expand(input_shape: Shape, shape: Shape) -> DimMap:
    """Implement broadcast on multiple dimensions."""
    from torch.fx.experimental.symbolic_shapes import guard_or_false

    if not len(shape) >= len(input_shape):
        raise AssertionError(
            f"Expected len(shape) >= len(input_shape), got {len(shape)} < {len(input_shape)}"
        )

    # 1. create padded input dimensions
    padded_input = dim_pad_left(len(input_shape), len(shape))
    # 2. check that input shapes are compatible
    mapping = []
    for p, desired_s in zip(padded_input, shape):
        if isinstance(p, Singleton):
            actual_s = 1
            if not desired_s >= 0:
                raise AssertionError(f"Expected desired_s >= 0, got {desired_s}")
        else:
            if not isinstance(p, InputDim):
                raise AssertionError(f"DimSpec not supported in expand: {p}")
            actual_s = input_shape[p.input_dim]
            if not (
                guard_or_false(actual_s == 1)
                or guard_or_false(desired_s == -1)
                or guard_or_false(desired_s == actual_s)
            ):
                raise AssertionError(
                    f"Expected actual_s == 1 or desired_s == -1 or "
                    f"desired_s == actual_s, got actual_s={actual_s}, desired_s={desired_s}"
                )
        mapping.append(
            p
            if (
                guard_or_false(desired_s == 1)
                or guard_or_false(desired_s == -1)
                or guard_or_false(desired_s == actual_s)
            )
            else Broadcast.new(p, desired_s)
        )
    return tuple(mapping)