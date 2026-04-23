def slice(inputs, start_indices, shape):
    inputs = get_ov_output(inputs)
    if isinstance(start_indices, (list, np.ndarray)):
        start_indices = tuple(start_indices)
    if isinstance(shape, (list, np.ndarray)):
        shape = tuple(shape)
    if not isinstance(start_indices, tuple):
        raise ValueError(
            "`slice` operation requires tuple for `start_indices with the "
            f"openvino backend. Received: start_indices={start_indices}"
        )
    if not isinstance(shape, tuple):
        raise ValueError(
            "`slice` operation requires tuple for `shape` with the "
            f"openvino backend. Received: shape={shape}"
        )

    axes = []
    start = []
    stop = []

    def prepare_slice_index(val):
        val_type = val.get_element_type()
        if not val_type.is_integral():
            raise ValueError(
                "`slice` is not supported by OpenVINO backend "
                "for `start_indices` or `shape` with non-integer types"
            )
        if val_type != Type.i32:
            val = ov_opset.convert(val, Type.i32).output(0)
        if len(val.get_partial_shape()) == 0:
            val = ov_opset.unsqueeze(
                val, ov_opset.constant(0, Type.i32)
            ).output(0)
        return val

    for idx, length in enumerate(shape):
        if length is not None and length >= 0:
            axes.append(idx)
            start_val = prepare_slice_index(get_ov_output(start_indices[idx]))
            stop_val = prepare_slice_index(
                get_ov_output(start_indices[idx] + length)
            )
            start.append(start_val)
            stop.append(stop_val)

    if len(axes) == 0:
        return inputs

    step = [1] * len(start)
    step = ov_opset.constant(step, Type.i32).output(0)
    start = ov_opset.concat(start, axis=0).output(0)
    stop = ov_opset.concat(stop, axis=0).output(0)
    axes = ov_opset.constant(axes, Type.i32).output(0)
    result = ov_opset.slice(inputs, start, stop, step, axes).output(0)

    # Apply reshape to ensure output matches expected shape
    # Convert None (dynamic) dimensions to -1 for OpenVINO compatibility
    if all(dim is None or (isinstance(dim, int) and dim >= 0) for dim in shape):
        reshape_pattern = [(-1 if dim is None else dim) for dim in shape]
        target_shape = ov_opset.constant(reshape_pattern, Type.i32).output(0)
        result = ov_opset.reshape(result, target_shape, False).output(0)

    return OpenVINOKerasTensor(result)