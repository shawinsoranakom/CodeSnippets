def quantize_helper(
    g: jit_utils.GraphContext,
    tensor: _C.Value,
    scale: _C.Value,
    zero_point: _C.Value,
    axis: _C.Value | None = None,
) -> _C.Value:
    """Appends to graph `g` ONNX nodes that quantizes `tensor` based on `scale`, `zero_point` and `axis`.

    Args:
        g: Graph, the ONNX IR graph that is under construction.
        tensor: torch._C.Value, representing the tensor to be quantized.
        scale: torch._C.Value, quantized scale.
        zero_point: torch._C.Value, quantized zero point.
        axis: Optional[torch._C.Value] default None, if None, represents per tensor quantization.
            Otherwise, represents per channel quantization, along given axis.

    Returns:
        A TupleConstruct storing information of the quantized tensor.
    """
    if (
        axis is not None
        and not _is_none(axis)
        and GLOBALS.export_onnx_opset_version < 13
    ):
        _onnx_opset_unsupported_detailed(
            "QuantizeLinear",
            GLOBALS.export_onnx_opset_version,
            13,
            "Attribute axis is not supported.",
            tensor,
        )

    if scale is None:
        raise AssertionError("scale must be non-None")
    if (
        _type_utils.JitScalarType.from_value(scale, _type_utils.JitScalarType.UNDEFINED)
        != _type_utils.JitScalarType.FLOAT
    ):
        scale = g.op("Cast", scale, to_i=_C_onnx.TensorProtoDataType.FLOAT)

    if zero_point is None:
        raise AssertionError("zero_point must be non-None")
    if _type_utils.JitScalarType.from_value(
        zero_point, _type_utils.JitScalarType.UNDEFINED
    ) not in {
        _type_utils.JitScalarType.UINT8,
        _type_utils.JitScalarType.INT8,
    }:
        zero_point = g.op("Cast", zero_point, to_i=_C_onnx.TensorProtoDataType.UINT8)
    output = g.op(
        "QuantizeLinear",
        tensor,
        scale,
        zero_point,
        axis_i=_get_const(axis, "i", "axis"),
    )
    args = [output, scale, zero_point]
    if axis is not None and not _is_none(axis):
        args.append(axis)
    return g.op("prim::TupleConstruct", *args)