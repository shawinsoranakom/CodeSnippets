def linspace(
    start, stop, num=50, endpoint=True, retstep=False, dtype=None, axis=0
):
    """Return evenly spaced numbers over a specified interval.

    Supports axis=0 (prepend) and axis=-1 (append). Intermediate axis values are
    treated as axis=-1.

    If `retstep` is True, also returns the step size between values.

    """

    start = get_ov_output(start)
    stop = get_ov_output(stop)

    if hasattr(num, "output") or isinstance(num, OpenVINOKerasTensor):
        num_tensor = get_ov_output(num)
        try:
            if num_tensor.get_node().get_type_name() == "Constant":
                num_value = num_tensor.get_node().get_vector()[0]
                num = int(num_value)
            else:
                raise NotImplementedError(
                    "Dynamic num values not fully supported"
                )
        except Exception as e:
            raise NotImplementedError(
                "Could not extract num value from tensor"
            ) from e
    else:
        num = int(num)

    if dtype is None:
        output_type = OPENVINO_DTYPES[config.floatx()]
    else:
        output_type = OPENVINO_DTYPES[dtype]

    start = ov_opset.convert(start, output_type).output(0)
    stop = ov_opset.convert(stop, output_type).output(0)

    if num < 0:
        raise ValueError("Number of samples, `num`, must be non-negative.")

    if num == 0:
        empty_shape = ov_opset.constant([0], Type.i32).output(0)
        result = ov_opset.broadcast(
            ov_opset.constant(0.0, output_type).output(0), empty_shape
        ).output(0)
        if retstep:
            nan_step = ov_opset.constant(np.nan, output_type).output(0)
            return OpenVINOKerasTensor(result), OpenVINOKerasTensor(nan_step)
        return OpenVINOKerasTensor(result)

    if num == 1:
        result_val = start
        axis_const = ov_opset.constant([axis], Type.i32).output(0)
        result = ov_opset.unsqueeze(result_val, axis_const).output(0)
        if retstep:
            if endpoint:
                step = ov_opset.constant(np.nan, output_type).output(0)
            else:
                step = ov_opset.subtract(stop, start).output(0)
            return OpenVINOKerasTensor(result), OpenVINOKerasTensor(step)
    zero_i32 = ov_opset.constant(0, Type.i32).output(0)
    one_i32 = ov_opset.constant(1, Type.i32).output(0)
    one_i32_array = ov_opset.constant([1], Type.i32).output(0)

    num_const = ov_opset.constant(num, output_type).output(0)

    if endpoint:
        divisor = ov_opset.subtract(
            num_const, ov_opset.constant(1, output_type).output(0)
        ).output(0)
    else:
        divisor = num_const

    step = ov_opset.divide(
        ov_opset.subtract(stop, start).output(0), divisor
    ).output(0)

    indices = ov_opset.range(
        zero_i32,
        ov_opset.constant(num, Type.i32).output(0),
        one_i32,
        output_type,
    ).output(0)

    start_shape = ov_opset.convert(
        ov_opset.shape_of(start).output(0), Type.i32
    ).output(0)
    indices_shape = ov_opset.convert(
        ov_opset.shape_of(indices).output(0), Type.i32
    ).output(0)

    start_rank = ov_opset.shape_of(start_shape).output(0)
    ones_for_start = ov_opset.broadcast(one_i32, start_rank).output(0)

    if axis == 0:
        indices_target_shape = ov_opset.concat(
            [indices_shape, ones_for_start], 0
        ).output(0)
        start_target_shape = ov_opset.concat(
            [one_i32_array, start_shape], 0
        ).output(0)
    else:
        indices_target_shape = ov_opset.concat(
            [ones_for_start, indices_shape], 0
        ).output(0)
        start_target_shape = ov_opset.concat(
            [start_shape, one_i32_array], 0
        ).output(0)

    indices_reshaped = ov_opset.reshape(
        indices, indices_target_shape, False
    ).output(0)
    start_reshaped = ov_opset.reshape(start, start_target_shape, False).output(
        0
    )
    step_reshaped = ov_opset.reshape(step, start_target_shape, False).output(0)

    scaled_indices = ov_opset.multiply(indices_reshaped, step_reshaped).output(
        0
    )
    result = ov_opset.add(start_reshaped, scaled_indices).output(0)

    if retstep:
        return OpenVINOKerasTensor(result), OpenVINOKerasTensor(step)
    return OpenVINOKerasTensor(result)