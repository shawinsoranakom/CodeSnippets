def flatten(g: jit_utils.GraphContext, input, start_dim, end_dim):
    dim = symbolic_helper._get_tensor_rank(input)
    if dim is None:
        return symbolic_helper._unimplemented(
            "dim",
            "ONNX and PyTorch use different strategies to split the input. "
            "Input rank must be known at export time.",
            input,
        )

    if dim == 0:
        return symbolic_helper._reshape_helper(g, input, [1])
    if dim == 1:
        return g.op("Identity", input)
    # TODO: remove this as onnx opset 11 spec allows negative axes
    if end_dim < 0:
        end_dim = dim + end_dim
    # use ONNX's Flatten operator for cases where the output shape is 2D
    if start_dim == 1 and end_dim == dim - 1:
        return g.op("Flatten", input, axis_i=start_dim)
    if start_dim == 0 and end_dim == dim - 2:
        return g.op("Flatten", input, axis_i=end_dim + 1)

    return symbolic_helper._flatten_helper(g, input, start_dim, end_dim, dim)