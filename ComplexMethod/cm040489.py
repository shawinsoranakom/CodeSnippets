def nanargmin(x, axis=None, keepdims=False):
    if isinstance(x, np.ndarray) and x.dtype == np.float64:
        # conversion to f32 due to https://github.com/openvinotoolkit/openvino/issues/34138
        x = x.astype(np.float32)
    x = get_ov_output(x)
    x_type = x.get_element_type()
    if x_type == Type.f64:
        # conversion to f32 due to https://github.com/openvinotoolkit/openvino/issues/34138
        x = ov_opset.convert(x, Type.f32).output(0)
        x_type = Type.f32

    original_axis = axis

    if x_type.is_integral() or x_type == Type.boolean:
        return argmin(
            OpenVINOKerasTensor(x), axis=original_axis, keepdims=keepdims
        )

    x, resolved_axis = _resolve_axis(x, original_axis)
    if resolved_axis is None:
        return OpenVINOKerasTensor(x)

    nan_mask = ov_opset.is_nan(x)
    pos_inf = ov_opset.constant(np.array(np.inf, dtype=np.float32))
    if x_type != Type.f32:
        pos_inf = ov_opset.convert(pos_inf, x_type)
    x_replaced = ov_opset.select(nan_mask, pos_inf, x).output(0)

    result = argmin(
        OpenVINOKerasTensor(x_replaced), axis=original_axis, keepdims=keepdims
    )
    result_ov = get_ov_output(result)

    all_nan = ov_opset.reduce_logical_and(
        nan_mask, resolved_axis, keepdims
    ).output(0)
    nan_value = ov_opset.constant(-1, Type.i32).output(0)
    if result_ov.get_element_type() != Type.i32:
        nan_value = ov_opset.convert(nan_value, result_ov.get_element_type())
    result_ov = ov_opset.select(all_nan, nan_value, result_ov).output(0)

    return OpenVINOKerasTensor(result_ov)