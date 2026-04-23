def einsum(subscripts, *operands, **kwargs):
    inputs = [get_ov_output(operand) for operand in operands]
    keras_types = [ov_to_keras_type(inp.get_element_type()) for inp in inputs]
    result_dtype = (
        dtypes.result_type(*keras_types) if keras_types else config.floatx()
    )
    if set(keras_types) == {"int8"}:
        result_dtype = "int32"
    ov_result_type = OPENVINO_DTYPES[result_dtype]
    # OV Einsum supports float*/int32/int64; promote unsupported types
    _ov_einsum_ok = {
        OPENVINO_DTYPES[t]
        for t in ("float16", "bfloat16", "float32", "float64", "int32", "int64")
    }
    if ov_result_type not in _ov_einsum_ok:
        ov_compute_type = OPENVINO_DTYPES[
            "int64" if result_dtype in ("uint32", "uint64") else "int32"
        ]
    else:
        ov_compute_type = ov_result_type
    inputs = [
        ov_opset.convert(inp, ov_compute_type).output(0)
        if inp.get_element_type() != ov_compute_type
        else inp
        for inp in inputs
    ]
    result = ov_opset.einsum(inputs, subscripts).output(0)
    if result.get_element_type() != ov_result_type:
        result = ov_opset.convert(result, ov_result_type).output(0)
    return OpenVINOKerasTensor(result)