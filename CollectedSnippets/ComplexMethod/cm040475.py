def arange(start, stop=None, step=None, dtype=None):
    # For concrete scalar inputs, delegate to NumPy directly (matches its
    # semantics exactly). Only build a graph for symbolic inputs.
    _symbolic_types = (OpenVINOKerasTensor, ov.Output, KerasVariable)
    _is_symbolic = (
        isinstance(start, _symbolic_types)
        or isinstance(stop, _symbolic_types)
        or isinstance(step, _symbolic_types)
    )
    if not _is_symbolic:
        _start = 0 if stop is None else start
        _stop = start if stop is None else stop
        _step = 1 if step is None else step
        keras_dtype = (
            standardize_dtype(dtype)
            if dtype is not None
            else dtypes.result_type(
                type(_start), type(_stop), type(_step), "int32"
            )
        )
        return OpenVINOKerasTensor(
            ov_opset.constant(
                np.arange(_start, _stop, _step, dtype=keras_dtype)
            ).output(0)
        )

    if stop is None:
        start, stop = get_ov_output(0), get_ov_output(start)
    else:
        start, stop = get_ov_output(start), get_ov_output(stop)

    step = get_ov_output(1) if step is None else get_ov_output(step)

    ov_type = None
    if dtype is not None:
        ov_type = OPENVINO_DTYPES[standardize_dtype(dtype)]
    else:
        ov_type = OPENVINO_DTYPES[
            dtypes.result_type(
                ov_to_keras_type(start.get_element_type()),
                ov_to_keras_type(stop.get_element_type()),
                ov_to_keras_type(step.get_element_type()),
                "int32",
            )
        ]

    start_node = ov_opset.convert(start, ov_type)
    stop_node = ov_opset.convert(stop, ov_type)
    step_node = ov_opset.convert(step, ov_type)

    return OpenVINOKerasTensor(
        ov_opset.range(start_node, stop_node, step_node, ov_type).output(0)
    )