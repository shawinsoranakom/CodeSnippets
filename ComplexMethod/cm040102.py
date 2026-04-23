def _analyze_split_string(
    split_string, bias_axes, input_shape, output_shape, left_elided=False
):
    """Computes kernel and bias shapes from a parsed einsum equation.

    This function takes the components of an einsum equation, validates them,
    and calculates the required shapes for the kernel and bias weights.

    Args:
        split_string: A regex match object containing the input, weight, and
            output specifications.
        bias_axes: A string indicating which output axes to apply a bias to.
        input_shape: The shape of the input tensor.
        output_shape: The user-specified partial shape of the output tensor.
        left_elided: A boolean indicating if the ellipsis "..." was on the
            left side of the equation.

    Returns:
        A tuple `(kernel_shape, bias_shape, full_output_shape)` where:
            `kernel_shape`: The calculated shape of the einsum kernel.
            `bias_shape`: The calculated shape of the bias, or `None`.
            `full_output_shape`: The fully-resolved shape of the output tensor.

    Raises:
        ValueError: If there are inconsistencies between the input and output
            shapes or if the equation specifications are invalid.
    """
    input_spec = split_string.group(1)
    weight_spec = split_string.group(2)
    output_spec = split_string.group(3)
    elided = len(input_shape) - len(input_spec)

    if isinstance(output_shape, int):
        output_shape = [output_shape]
    else:
        output_shape = list(output_shape)

    output_shape.insert(0, input_shape[0])

    if elided > 0 and left_elided:
        for i in range(1, elided):
            # We already inserted the 0th input dimension at dim 0, so we need
            # to start at location 1 here.
            output_shape.insert(1, input_shape[i])
    elif elided > 0 and not left_elided:
        for i in range(len(input_shape) - elided, len(input_shape)):
            output_shape.append(input_shape[i])

    if left_elided:
        # If we have beginning dimensions elided, we need to use negative
        # indexing to determine where in the input dimension our values are.
        input_dim_map = {
            dim: (i + elided) - len(input_shape)
            for i, dim in enumerate(input_spec)
        }
        # Because we've constructed the full output shape already, we don't need
        # to do negative indexing.
        output_dim_map = {
            dim: (i + elided) for i, dim in enumerate(output_spec)
        }
    else:
        input_dim_map = {dim: i for i, dim in enumerate(input_spec)}
        output_dim_map = {dim: i for i, dim in enumerate(output_spec)}

    for dim in input_spec:
        input_shape_at_dim = input_shape[input_dim_map[dim]]
        if dim in output_dim_map:
            output_shape_at_dim = output_shape[output_dim_map[dim]]
            if (
                output_shape_at_dim is not None
                and output_shape_at_dim != input_shape_at_dim
            ):
                raise ValueError(
                    "Input shape and output shape do not match at shared "
                    f"dimension '{dim}'. Input shape is {input_shape_at_dim}, "
                    "and output shape "
                    f"is {output_shape[output_dim_map[dim]]}."
                )

    for dim in output_spec:
        if dim not in input_spec and dim not in weight_spec:
            raise ValueError(
                f"Dimension '{dim}' was specified in the output "
                f"'{output_spec}' but has no corresponding dim in the input "
                f"spec '{input_spec}' or weight spec '{output_spec}'"
            )

    weight_shape = []
    for dim in weight_spec:
        if dim in input_dim_map:
            weight_shape.append(input_shape[input_dim_map[dim]])
        elif dim in output_dim_map:
            weight_shape.append(output_shape[output_dim_map[dim]])
        else:
            raise ValueError(
                f"Weight dimension '{dim}' did not have a match in either "
                f"the input spec '{input_spec}' or the output "
                f"spec '{output_spec}'. For this layer, the weight must "
                "be fully specified."
            )

    if bias_axes is not None:
        num_left_elided = elided if left_elided else 0
        idx_map = {
            char: output_shape[i + num_left_elided]
            for i, char in enumerate(output_spec)
        }

        for char in bias_axes:
            if char not in output_spec:
                raise ValueError(
                    f"Bias dimension '{char}' was requested, but is not part "
                    f"of the output spec '{output_spec}'"
                )

        first_bias_location = min(
            [output_spec.find(char) for char in bias_axes]
        )
        bias_output_spec = output_spec[first_bias_location:]

        bias_shape = [
            idx_map[char] if char in bias_axes else 1
            for char in bias_output_spec
        ]

        if not left_elided:
            for _ in range(elided):
                bias_shape.append(1)
    else:
        bias_shape = None

    return weight_shape, bias_shape, output_shape