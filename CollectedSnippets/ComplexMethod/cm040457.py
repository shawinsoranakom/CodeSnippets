def convert_to_numpy(x):
    if isinstance(x, np.ndarray):
        return x
    elif isinstance(x, (int, float)):
        return np.array(x)
    elif isinstance(x, (list, tuple)):
        x_new = []
        for elem in x:
            x_new.append(convert_to_numpy(elem))
        return np.array(x_new)
    elif np.isscalar(x):
        return x
    elif isinstance(x, ov.Tensor):
        return x.data
    elif x is None:
        return x
    elif isinstance(x, KerasVariable):
        if isinstance(x.value, OpenVINOKerasTensor):
            x = x.value
        else:
            return x.value.data
    if not isinstance(x, OpenVINOKerasTensor):
        raise ValueError(f"unsupported type {type(x)} for `convert_to_numpy`.")
    # if the tensor is backed by a Constant OV node, extract
    # its data array directly without compiling a model.
    try:
        node = x.output.get_node()
        if node.get_type_name() == "Constant":
            data = node.data
            # OpenVINO returns bf16 constant bytes as float16 (same width,
            # but wrong dtype) because numpy has no native bfloat16 type.
            # Re-interpret the raw bytes as ml_dtypes.bfloat16.
            if node.output(0).get_element_type() == Type.bf16:
                data = data.view(ml_dtypes.bfloat16)
            return np.array(data)
    except Exception:
        # fall back to the slow path.
        pass
    try:
        ov_result = x.output
        casted_from_bool = False
        if ov_result.get_element_type() == Type.boolean:
            ov_result = ov_opset.convert(ov_result, Type.i32).output(0)
            casted_from_bool = True
        ov_model = Model(results=[ov_result], parameters=[])
        ov_compiled_model = compile_model(
            ov_model,
            get_device(),
            config={"INFERENCE_PRECISION_HINT": "f32"},
        )
        result = ov_compiled_model({})[0]
        if casted_from_bool:
            result = result.astype(bool)
    except Exception as inner_exception:
        raise RuntimeError(
            "`convert_to_numpy` failed to convert the tensor."
        ) from inner_exception
    data = np.array(result)
    # Same byte-reinterpretation issue applies to inference results.
    if x.dtype == "bfloat16" and data.dtype != ml_dtypes.bfloat16:
        data = data.view(ml_dtypes.bfloat16)
    return data