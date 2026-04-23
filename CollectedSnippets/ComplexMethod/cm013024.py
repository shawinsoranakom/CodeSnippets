def flatten(g: jit_utils.GraphContext, input, start_dim, end_dim):
    dim = symbolic_helper._get_tensor_rank(input)
    if dim == 1:
        return input
    # use ONNX's Flatten operator for cases where the output shape is 2D
    if start_dim == 1:
        if end_dim == -1 or (dim is not None and end_dim == dim - 1):
            return g.op("Flatten", input, axis_i=start_dim)
    elif start_dim == 0:
        if end_dim == -2 or (dim is not None and end_dim == dim - 2):
            return g.op("Flatten", input, axis_i=end_dim + 1)
    if dim is None:
        return symbolic_helper._unimplemented(
            "dim",
            "ONNX and PyTorch use different strategies to split the input. "
            "Input rank must be known at export time.",
        )
    # if end_dim is negative add dim
    if end_dim < 0:
        end_dim = dim + end_dim

    return symbolic_helper._flatten_helper(g, input, start_dim, end_dim, dim)