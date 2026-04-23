def nanmin(x, axis=None, keepdims=False):
    if isinstance(x, np.ndarray) and x.dtype == np.float64:
        # conversion to f32 due to https://github.com/openvinotoolkit/openvino/issues/34138
        x = x.astype(np.float32)
    x = get_ov_output(x)
    x_type = x.get_element_type()
    if x_type == Type.f64:
        # conversion to f32 due to https://github.com/openvinotoolkit/openvino/issues/34138
        x = ov_opset.convert(x, Type.f32).output(0)
        x_type = Type.f32

    if x_type.is_integral() or x_type == Type.boolean:
        return amin(OpenVINOKerasTensor(x), axis=axis, keepdims=keepdims)

    x, axis = _resolve_axis(x, axis)
    if axis is None:
        return OpenVINOKerasTensor(x)

    nan_mask = ov_opset.is_nan(x)
    pos_inf = ov_opset.constant(np.array(np.inf, dtype=np.float32))
    if x_type != Type.f32:
        pos_inf = ov_opset.convert(pos_inf, x_type)
    x_replaced = ov_opset.select(nan_mask, pos_inf, x).output(0)

    result = ov_opset.reduce_min(x_replaced, axis, keepdims).output(0)

    all_nan = ov_opset.reduce_logical_and(nan_mask, axis, keepdims).output(0)
    nan_value = ov_opset.constant(np.array(np.nan, dtype=np.float32))
    if x_type != Type.f32:
        nan_value = ov_opset.convert(nan_value, x_type)
    result = ov_opset.select(all_nan, nan_value, result).output(0)

    return OpenVINOKerasTensor(result)