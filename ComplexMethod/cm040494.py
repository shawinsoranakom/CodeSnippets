def nanvar(x, axis=None, keepdims=False):
    x = get_ov_output(x)
    x_type = x.get_element_type()
    x_keras = ov_to_keras_type(x_type)
    result_dtype = dtypes.result_type(x_keras, float)
    ov_result_type = OPENVINO_DTYPES[result_dtype]

    # Compute in float32 due to OpenVINO f64 limitation
    if x_type == Type.f64:
        x = ov_opset.convert(x, Type.f32).output(0)
        x_type = Type.f32

    if x_type.is_integral() or x_type == Type.boolean:
        result = var(OpenVINOKerasTensor(x), axis=axis, keepdims=keepdims)
        result = get_ov_output(result)
        if result.get_element_type() != ov_result_type:
            result = ov_opset.convert(result, ov_result_type).output(0)
        return OpenVINOKerasTensor(result)

    if axis == () or axis == []:
        nan_mask = ov_opset.is_nan(x).output(0)
        zero = ov_opset.constant(0, x_type).output(0)
        result = ov_opset.select(nan_mask, x, zero).output(0)
        if x_type != ov_result_type:
            result = ov_opset.convert(result, ov_result_type).output(0)
        return OpenVINOKerasTensor(result)

    # Compute mean ignoring NaN, keeping dims for broadcasting
    mean_val = get_ov_output(
        nanmean(OpenVINOKerasTensor(x), axis=axis, keepdims=True)
    )

    nan_mask = ov_opset.is_nan(x)
    zero = ov_opset.constant(0, x_type)
    not_nan = ov_opset.logical_not(nan_mask).output(0)

    # Squared deviations, zeroed where NaN
    centered = ov_opset.subtract(x, mean_val).output(0)
    centered = ov_opset.select(nan_mask, zero, centered).output(0)
    squared = ov_opset.multiply(centered, centered).output(0)

    if axis is None:
        flatten_shape = ov_opset.constant([-1], Type.i32).output(0)
        squared = ov_opset.reshape(squared, flatten_shape, False).output(0)
        not_nan = ov_opset.reshape(not_nan, flatten_shape, False).output(0)
        axis_const = ov_opset.constant(0, Type.i32).output(0)
    else:
        if isinstance(axis, (tuple, list)):
            axis_const = ov_opset.constant(list(axis), Type.i32).output(0)
        else:
            axis_const = ov_opset.constant(axis, Type.i32).output(0)

    not_nan_float = ov_opset.convert(not_nan, x_type).output(0)
    sq_sum = ov_opset.reduce_sum(squared, axis_const, keepdims).output(0)
    count = ov_opset.reduce_sum(not_nan_float, axis_const, keepdims).output(0)
    result = ov_opset.divide(sq_sum, count).output(0)
    if result.get_element_type() != ov_result_type:
        result = ov_opset.convert(result, ov_result_type).output(0)
    return OpenVINOKerasTensor(result)