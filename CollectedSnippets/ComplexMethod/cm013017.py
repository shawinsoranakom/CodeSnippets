def flatten(g: jit_utils.GraphContext, input, start_dim, end_dim):
    start_dim_i = symbolic_helper._get_const(start_dim, "i", "start_dim")
    end_dim_i = symbolic_helper._get_const(end_dim, "i", "end_dim")

    dim = input.type().dim()
    if end_dim_i < 0:
        end_dim_i = dim + end_dim_i
    # use ONNX's Flatten operator for cases where the output shape is 2D
    if start_dim_i == 1 and end_dim_i == dim - 1:
        if symbolic_helper._try_get_scalar_type(input):
            old_type, input = _try_cast_integer_to_float(g, input)
            return _cast_to_type(
                g, g.op("Flatten", input, axis_i=start_dim_i), old_type
            )
        else:
            return g.op("Flatten", input, axis_i=start_dim_i)
    if start_dim_i == 0 and end_dim_i == dim - 2:
        if symbolic_helper._try_get_scalar_type(input):
            old_type, input = _try_cast_integer_to_float(g, input)
            return _cast_to_type(
                g, g.op("Flatten", input, axis_i=end_dim_i + 1), old_type
            )
        else:
            return g.op("Flatten", input, axis_i=end_dim_i + 1)

    return opset9.flatten(g, input, start_dim, end_dim)