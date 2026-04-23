def tensor(
    g: jit_utils.GraphContext, data, dtype=None, device=None, requires_grad=False
):
    dtype = symbolic_helper._get_const(dtype, "i", "dtype")
    if symbolic_helper._is_packed_list(data):
        if dtype is None:
            dtype = _type_utils.JitScalarType.from_value(
                symbolic_helper._unpack_list(data)[0]
            )
        input_list = []
        for t in symbolic_helper._unpack_list(data):
            shape_reference = g.op("Constant", value_t=torch.LongTensor([1]))
            t = symbolic_helper._reshape_helper(g, t, shape_reference)
            t = g.op("Cast", t, to_i=_type_utils.JitScalarType(dtype).onnx_type())
            input_list.append(t)
        return g.op("Concat", *input_list, axis_i=0)
    else:
        if dtype is None:
            dtype = _type_utils.JitScalarType.from_value(data)
        if symbolic_helper._is_list(data) and (
            symbolic_helper._is_tensor_list(data)
            or symbolic_helper._is_scalar_list(data)
        ):
            data = g.op("ConcatFromSequence", data, axis_i=0, new_axis_i=1)
    return g.op("Cast", data, to_i=_type_utils.JitScalarType(dtype).onnx_type())