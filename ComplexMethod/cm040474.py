def _compute_extrema(x, operation, axis=None, keepdims=False, initial=None):
    if operation == "min":
        reduction_op = ov_opset.reduce_min
        elementwise_op = ov_opset.minimum
    elif operation == "max":
        reduction_op = ov_opset.reduce_max
        elementwise_op = ov_opset.maximum
    else:
        raise ValueError(
            f"Operation must be 'min' or 'max', received {operation}"
        )

    x = get_ov_output(x)
    x_type = x.get_element_type()
    x_for_rank = x

    is_bool = x_type == Type.boolean
    if is_bool:
        x = ov_opset.convert(x, Type.i32).output(0)
        x_type = Type.i32

    if isinstance(axis, tuple) and len(axis) == 0:
        return OpenVINOKerasTensor(x)

    was_axis_none = axis is None
    x, axis = _resolve_axis(x, axis)

    result = reduction_op(x, axis, keepdims).output(0)

    if initial is not None:
        initial_tensor = ov_opset.constant(initial, x_type).output(0)
        result = elementwise_op(result, initial_tensor).output(0)

    if keepdims and was_axis_none:
        orig_shape = ov_opset.shape_of(x_for_rank, Type.i32).output(0)
        orig_rank_shape = ov_opset.shape_of(orig_shape, Type.i32).output(0)
        one = ov_opset.constant(1, Type.i32).output(0)
        result_shape = ov_opset.broadcast(one, orig_rank_shape).output(0)
        result = ov_opset.reshape(result, result_shape, False).output(0)

    if is_bool:
        result = ov_opset.convert(result, Type.boolean).output(0)

    return OpenVINOKerasTensor(result)