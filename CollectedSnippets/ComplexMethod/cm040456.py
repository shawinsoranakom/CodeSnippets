def convert_to_tensor(x, dtype=None, sparse=None, ragged=None):
    if sparse:
        raise ValueError("`sparse=True` is not supported with openvino backend")
    if ragged:
        raise ValueError("`ragged=True` is not supported with openvino backend")
    if dtype is not None:
        dtype = standardize_dtype(dtype)
    if isinstance(x, OpenVINOKerasTensor):
        if dtype and dtype != standardize_dtype(x.dtype):
            x = cast(x, dtype)
        return x
    elif isinstance(x, np.ndarray):
        if dtype is not None:
            ov_type = OPENVINO_DTYPES[dtype]
        else:
            ov_type = OPENVINO_DTYPES[standardize_dtype(x.dtype)]
        return OpenVINOKerasTensor(ov_opset.constant(x, ov_type).output(0))
    elif isinstance(x, (list, tuple)):
        if dtype is None:
            dtype = result_type(
                *[
                    getattr(item, "dtype", type(item))
                    for item in tree.flatten(x)
                ]
            )
        x = np.array(x, dtype=dtype)
        ov_type = OPENVINO_DTYPES[dtype]
        return OpenVINOKerasTensor(ov_opset.constant(x, ov_type).output(0), x)
    elif isinstance(x, (float, int, bool)):
        if dtype is None:
            dtype = standardize_dtype(type(x))
        ov_type = OPENVINO_DTYPES[dtype]
        return OpenVINOKerasTensor(ov_opset.constant(x, ov_type).output(0), x)
    elif isinstance(x, ov.Output):
        return OpenVINOKerasTensor(x)
    if isinstance(x, Variable):
        x = x.value
        if dtype and dtype != x.dtype:
            x = cast(x, dtype)
        return x
    original_type = type(x)
    try:
        if dtype is None:
            dtype = getattr(x, "dtype", original_type)
            ov_type = OPENVINO_DTYPES[standardize_dtype(dtype)]
        else:
            ov_type = OPENVINO_DTYPES[dtype]
        x = np.array(x)
        return OpenVINOKerasTensor(ov_opset.constant(x, ov_type).output(0))
    except Exception as e:
        raise TypeError(
            f"Cannot convert object of type {original_type} "
            f"to OpenVINOKerasTensor: {e}"
        )