def meshgrid(g: jit_utils.GraphContext, tensor_list, indexing: str | None = None):
    if indexing is None:
        indexing = "ij"
    elif indexing not in {"ij", "xy"}:
        raise errors.SymbolicValueError(
            f"Unsupported indexing: {indexing}", tensor_list
        )
    unpacked_tensor_list = symbolic_helper._unpack_list(tensor_list)
    if indexing == "xy":
        unpacked_tensor_list[:2] = unpacked_tensor_list[1::-1]
    tensors = [
        symbolic_helper._reshape_helper(
            g, t, g.op("Constant", value_t=torch.LongTensor([-1]))
        )
        for t in unpacked_tensor_list
    ]
    tensors_shape = [g.op("Shape", t) for t in tensors]
    out_shape = g.op("Concat", *tensors_shape, axis_i=0)
    out = []
    for i, t in enumerate(tensors):
        shape_i = [g.op("Constant", value_t=torch.ones(1, dtype=torch.int64))] * len(
            tensors
        )
        shape_i[i] = tensors_shape[i]
        t_reshaped = _reshape_from_tensor(g, t, g.op("Concat", *shape_i, axis_i=0))
        out.append(g.op("Expand", t_reshaped, out_shape))
    if indexing == "xy":
        out[0], out[1] = out[1], out[0]
    return g.op("prim::ListConstruct", *out)