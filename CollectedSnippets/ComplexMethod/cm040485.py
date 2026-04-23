def median(x, axis=None, keepdims=False):
    x = get_ov_output(x)
    x_shape = x.get_partial_shape()
    rank = x_shape.rank.get_length()

    if rank == 0:
        return OpenVINOKerasTensor(x)

    # Handle axis=None by flattening the input
    flattened_all = False
    if axis is None:
        x = ov_opset.reshape(x, [-1], False).output(0)
        axis = 0
        original_rank = rank
        rank = 1
        flattened_all = True
    else:
        # Handle tuple axis - for median, we only support single axis
        if isinstance(axis, (tuple, list)):
            if len(axis) != 1:
                raise ValueError("median only supports single axis reduction")
            axis = axis[0]

        # Handle negative axis
        if axis < 0:
            axis = rank + axis
        original_rank = rank

    # Get the size of the dimension to sort
    shape_tensor = ov_opset.shape_of(x, output_type=Type.i32).output(0)
    k = ov_opset.gather(
        shape_tensor,
        ov_opset.constant([axis], Type.i32).output(0),
        ov_opset.constant(0, Type.i32).output(0),
    ).output(0)

    # Convert k to a scalar value
    k_scalar = ov_opset.squeeze(k, [0]).output(0)

    # Use topk with k=size_of_axis to get all elements sorted
    topk_outputs = ov_opset.topk(
        x, k=k_scalar, axis=axis, mode="min", sort="value", stable=True
    )

    # Get the sorted values
    sorted_values = topk_outputs.output(0)

    # Convert to float for median calculation
    x1_type = ov_to_keras_type(sorted_values.get_element_type())
    result_type = dtypes.result_type(x1_type, float)
    result_type = OPENVINO_DTYPES[result_type]
    sorted_values = ov_opset.convert(sorted_values, result_type).output(0)

    # Calculate median indices
    # For odd length: median_idx = (k-1) // 2
    # For even length: we need indices (k//2 - 1) and k//2, then average

    k_minus_1 = ov_opset.subtract(
        k_scalar, ov_opset.constant(1, Type.i32).output(0)
    ).output(0)
    k_div_2 = ov_opset.divide(
        k_scalar, ov_opset.constant(2, Type.i32).output(0)
    ).output(0)
    k_minus_1_div_2 = ov_opset.divide(
        k_minus_1, ov_opset.constant(2, Type.i32).output(0)
    ).output(0)

    # Check if k is odd
    k_mod_2 = ov_opset.mod(
        k_scalar, ov_opset.constant(2, Type.i32).output(0)
    ).output(0)
    is_odd = ov_opset.equal(
        k_mod_2, ov_opset.constant(1, Type.i32).output(0)
    ).output(0)

    # For odd case: take the middle element
    odd_idx = k_minus_1_div_2

    # For even case: take average of two middle elements
    even_idx1 = ov_opset.subtract(
        k_div_2, ov_opset.constant(1, Type.i32).output(0)
    ).output(0)
    even_idx2 = k_div_2

    # Gather elements for both cases
    # Create gather indices tensor for the axis
    gather_indices_odd = ov_opset.unsqueeze(odd_idx, [0]).output(0)
    gather_indices_even1 = ov_opset.unsqueeze(even_idx1, [0]).output(0)
    gather_indices_even2 = ov_opset.unsqueeze(even_idx2, [0]).output(0)

    # Gather the median elements
    odd_result = ov_opset.gather(
        sorted_values,
        gather_indices_odd,
        ov_opset.constant(axis, Type.i32).output(0),
    ).output(0)
    even_result1 = ov_opset.gather(
        sorted_values,
        gather_indices_even1,
        ov_opset.constant(axis, Type.i32).output(0),
    ).output(0)
    even_result2 = ov_opset.gather(
        sorted_values,
        gather_indices_even2,
        ov_opset.constant(axis, Type.i32).output(0),
    ).output(0)

    # Average the two middle elements for even case
    even_sum = ov_opset.add(even_result1, even_result2).output(0)
    even_result = ov_opset.divide(
        even_sum, ov_opset.constant(2.0, result_type).output(0)
    ).output(0)

    # Select between odd and even results
    median_result = ov_opset.select(is_odd, odd_result, even_result).output(0)

    # Remove the gathered dimension (squeeze)
    median_result = ov_opset.squeeze(median_result, [axis]).output(0)

    # Handle keepdims
    if keepdims:
        if flattened_all:
            # When axis=None, keepdims should restore all dimensions as 1
            ones_shape = ov_opset.constant(
                [1] * original_rank, Type.i32
            ).output(0)
            median_result = ov_opset.reshape(
                median_result, ones_shape, False
            ).output(0)
        else:
            median_result = ov_opset.unsqueeze(median_result, [axis]).output(0)

    return OpenVINOKerasTensor(median_result)