def get_ov_output(x, ov_type=None, context_dtype=None):
    if (
        isinstance(x, (float, int))
        and ov_type is None
        and context_dtype is not None
    ):
        ov_type = OPENVINO_DTYPES[dtypes.result_type(context_dtype, type(x))]
    if isinstance(x, float):
        if ov_type is None:
            ov_type = Type.f32
        if ov_type == Type.bf16:
            x = ov_opset.constant(x, Type.f32).output(0)
            x = ov_opset.convert(x, Type.bf16).output(0)
        else:
            x = ov_opset.constant(x, ov_type).output(0)
    elif isinstance(x, int):
        if ov_type is None:
            ov_type = Type.i32
        if ov_type == Type.bf16:
            x = ov_opset.constant(float(x), Type.f32).output(0)
            x = ov_opset.convert(x, Type.bf16).output(0)
        else:
            x = ov_opset.constant(x, ov_type).output(0)
    elif isinstance(x, np.ndarray):
        if x.dtype == "bfloat16":
            x = ov_opset.constant(x, OPENVINO_DTYPES["bfloat16"]).output(0)
        else:
            x = ov_opset.constant(x).output(0)
    elif isinstance(x, (list, tuple)):
        if isinstance(x, tuple):
            x = list(x)
        if ov_type is None:
            x = ov_opset.constant(x).output(0)
        else:
            x = ov_opset.constant(x, ov_type).output(0)
    elif np.isscalar(x):
        x = ov_opset.constant(x).output(0)
    elif isinstance(x, KerasVariable):
        if isinstance(x.value, OpenVINOKerasTensor):
            return x.value.output
        x = ov_opset.constant(x.value.data).output(0)
    elif isinstance(x, OpenVINOKerasTensor):
        x = x.output
    elif isinstance(x, ov.Output):
        return x
    elif isinstance(x, Tensor):
        x = ov_opset.constant(x.data).output(0)
    else:
        raise ValueError(
            "unsupported type of `x` to create ov.Output: {}".format(type(x))
        )
    return x