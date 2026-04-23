def compute_quantization_parameters(
    x,
    *,
    bits,
    symmetric=False,
    per_channel=False,
    group_size=-1,
    compute_dtype="float32",
    epsilon=0.0,
    signed=False,
):
    """
    Computes the scale and zero-point for quantizing weight tensors.

    This function calculates the scale and zero-point required for quantizing
    a given weight tensor `x` based on the specified parameters. It supports
    grouped, per-channel, per-tensor, symmetric, and asymmetric quantization.

    For grouped quantization (per_channel=True, group_size > 0), the output
    shapes are [out_features, n_groups] where n_groups is the number of groups
    along the in_features dimension.

    Args:
        x: KerasTensor. The weight tensor to quantize with shape
            [out_features, in_features].
        bits: int. The number of bits to quantize to (e.g., 4).
        symmetric: bool. Whether to use symmetric quantization.
        per_channel: bool. Whether to quantize per channel.
        group_size: int. The group size for quantization. -1 means no grouping.
        compute_dtype: str. The dtype for computation. Defaults to "float32".
        epsilon: float. Small value added to (max - min) before computing
            scale to avoid division by zero. Defaults to 0.0.
        signed: bool. Whether to use signed quantization range. If True, uses
            range [-2^(bits-1), 2^(bits-1)-1] (e.g., [-8, 7] for 4-bit).
            If False, uses range [0, 2^bits-1] (e.g., [0, 15] for 4-bit).
            Defaults to False.

    Returns:
        scale: KerasTensor. The scale tensor for quantization.
        zero: KerasTensor. The zero tensor for quantization (int8 if signed,
            uint8 if unsigned).
        maxq: scalar. The maximum quantization value.
    """
    # Input validation
    if x is None:
        raise ValueError(f"Input tensor {x} cannot be None.")
    if len(x.shape) < 2:
        raise ValueError(
            f"Input weight tensor {x} must have a rank of at "
            f"least 2, but got rank {len(x.shape)}."
        )
    if ops.size(x) == 0:
        raise ValueError("Input tensor 'x' cannot be empty.")

    out_features, in_features = x.shape[0], x.shape[1]

    # Determine number of groups for quantization
    if per_channel and group_size > 0:
        n_groups = (in_features + group_size - 1) // group_size
    else:
        n_groups = 1

    # Compute min/max values based on quantization mode
    if n_groups > 1:
        # Grouped quantization: output shape [out_features, n_groups]
        remainder = in_features % group_size
        if remainder != 0:
            pad_size = group_size - remainder
            x = ops.pad(x, [[0, 0], [0, pad_size]], constant_values=0.0)

        x_grouped = ops.reshape(x, [out_features, n_groups, group_size])
        min_values = ops.min(x_grouped, axis=2)
        max_values = ops.max(x_grouped, axis=2)
    else:
        # Per-channel or per-tensor: compute stats along rows
        reduction_shape = [out_features, -1] if per_channel else [1, -1]
        x_reshaped = ops.reshape(x, reduction_shape)
        min_values = ops.min(x_reshaped, axis=1)
        max_values = ops.max(x_reshaped, axis=1)

    # Symmetric quantization: make range symmetric around zero
    if symmetric:
        max_abs = ops.maximum(ops.abs(min_values), max_values)
        min_values = ops.where(
            ops.less(min_values, 0), ops.negative(max_abs), min_values
        )
        max_values = max_abs

    # Ensure non-zero range to avoid division errors
    zero_range = ops.equal(min_values, max_values)
    min_values = ops.where(zero_range, ops.subtract(min_values, 1), min_values)
    max_values = ops.where(zero_range, ops.add(max_values, 1), max_values)

    # Compute scale and zero-point
    maxq = ops.cast(ops.subtract(ops.power(2, bits), 1), compute_dtype)
    range_values = ops.subtract(max_values, min_values)
    if epsilon > 0:
        range_values = ops.add(range_values, epsilon)
    scale = ops.divide(range_values, maxq)
    scale = ops.where(ops.less_equal(scale, 0), 1e-8, scale)

    # Compute zero-point based on signed/unsigned mode
    if signed:
        # For signed range [-2^(bits-1), 2^(bits-1)-1], e.g., [-8, 7] for 4-bit
        qmin = -(2 ** (bits - 1))  # e.g., -8 for 4-bit
        qmax_signed = 2 ** (bits - 1) - 1  # e.g., 7 for 4-bit
        if symmetric:
            zero = ops.full_like(scale, ops.divide(ops.add(maxq, 1), 2) + qmin)
        else:
            # zero_signed = round(-min / scale) + qmin
            zero = ops.add(
                ops.round(ops.divide(ops.negative(min_values), scale)), qmin
            )
        zero = ops.clip(zero, qmin, qmax_signed)
    else:
        # For unsigned range [0, 2^bits-1], e.g., [0, 15] for 4-bit
        if symmetric:
            zero = ops.full_like(scale, ops.divide(ops.add(maxq, 1), 2))
        else:
            zero = ops.round(ops.divide(ops.negative(min_values), scale))

    # Reshape output to [out_features, n_groups] or [out_features, 1]
    if n_groups > 1:
        pass  # Already [out_features, n_groups]
    elif per_channel:
        scale = ops.reshape(scale, [-1, 1])
        zero = ops.reshape(zero, [-1, 1])
    else:
        # Per-tensor: tile single value to [out_features, 1]
        scale = ops.tile(ops.reshape(scale, (1, 1)), (out_features, 1))
        zero = ops.tile(ops.reshape(zero, (1, 1)), (out_features, 1))

    zero_dtype = "int8" if signed else "uint8"
    return scale, ops.cast(zero, zero_dtype), maxq