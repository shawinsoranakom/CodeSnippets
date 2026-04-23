def softmax(g: jit_utils.GraphContext, input, dim, dtype=None):
    # Softmax does normalization at vector level.
    # PyTorch and ONNX use different strategies to split the input tensor into vectors.
    # Thus dim and axis have different meanings.
    # PyTorch slices the input tensor into vectors along the `dim`-th dimension.
    # ONNX reshapes the input into a 2-D tensor, and `axis` indicates where the input is coerced.
    # If input is a 2 x 3 tensor:
    # input = [[1.0, 1.0, 1.0],
    #          [1.0, 1,0, 1,0]]
    # with dim = 0, the result is:
    # result = [[0.5, 0.5, 0.5],
    #           [0.5, 0.5, 0.5]]
    # with axis = 0, the result is:
    # result = [[0.167, 0.167, 0.167],
    #           [0.167, 0.167, 0.167]]
    # So only when dim and axis both equal to ndim - 1 (the last dimension),
    # their semantics are equivalent.
    # So use softmax when dim and axis both equal to ndim - 1,
    # otherwise transpose the input to put the vectors to be normalized to the last dimension.
    # When input rank is not known at export time we compute softmax using a subgraph
    # with other operators
    input_dim = symbolic_helper._get_tensor_rank(input)
    if input_dim is not None:
        # TODO: remove this as onnx opset 11 spec allows negative axes
        if dim < 0:
            dim = input_dim + dim

        is_transpose_required = input_dim != dim + 1

        if is_transpose_required:
            axes = list(range(input_dim))
            axes[dim], axes[-1] = axes[-1], axes[dim]
            input = g.op("Transpose", input, perm_i=axes)
            dim = input_dim - 1

        softmax = g.op("Softmax", input, axis_i=dim)
        if dtype and dtype.node().kind() != "prim::Constant":
            parsed_dtype = symbolic_helper._get_const(dtype, "i", "dtype")
            softmax = g.op(
                "Cast",
                softmax,
                to_i=_type_utils.JitScalarType(parsed_dtype).onnx_type(),
            )

        if is_transpose_required:
            softmax = g.op("Transpose", softmax, perm_i=axes)  # type: ignore[possibly-undefined]
        return softmax

    # Apply max normalization.
    input = g.op("Sub", input, g.op("ReduceMax", input, axes_i=[dim], keepdims_i=1))

    exp = g.op("Exp", input)
    sum = symbolic_helper._reducesum_helper(g, exp, axes_i=[dim])
    softmax = g.op("Div", exp, sum)
    if dtype and dtype.node().kind() != "prim::Constant":
        parsed_dtype = symbolic_helper._get_const(dtype, "i", "dtype")
        softmax = g.op(
            "Cast", softmax, to_i=_type_utils.JitScalarType(parsed_dtype).onnx_type()
        )
    return softmax