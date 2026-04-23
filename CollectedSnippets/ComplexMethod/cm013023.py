def squeeze(g: jit_utils.GraphContext, self, dim=None):
    if dim is None:
        return g.op("Squeeze", self)

    # dim as a tensor
    if not symbolic_helper._is_constant(dim):
        return symbolic_helper._squeeze_helper(g, self, [dim])

    dim = symbolic_helper._get_const(dim, "i", "dim")

    input_rank = symbolic_helper._get_tensor_rank(self)
    adjusted_dim = dim
    if input_rank is not None and dim < 0:
        adjusted_dim += input_rank
    dim_size = symbolic_helper._get_tensor_dim_size(self, adjusted_dim)
    if (dim < 0 and input_rank is None) or dim_size is None:
        # If onnx shape inference is not on, export always as dynamic.
        # Because we cannot tell if observed static shape is also static at runtime.
        # create "cond" node (condition is shape[i]==1)
        dim_constant = g.op("Constant", value_t=torch.tensor([dim]))
        size = symbolic_helper._size_helper(g, self, dim_constant)
        const_one = g.op("Constant", value_t=torch.ones(1, dtype=torch.int64))
        cond = g.op("Equal", size, const_one)
        # create the "If" node and add the "then" and "else" blocks to it.
        if_op, (if_context, else_context), _ = jit_utils.add_op_with_blocks(
            g, "If", cond, n_blocks=2
        )
        squeeze_ = symbolic_helper._squeeze_helper(if_context, self, [dim])
        utils._add_output_to_block(if_context.block, squeeze_)
        identity_ = else_context.op("Identity", self)
        utils._add_output_to_block(else_context.block, identity_)
        return if_op

    # For static input shape
    dim = adjusted_dim
    if dim_size > 1:
        warnings.warn(
            "This model contains a squeeze operation on dimension "
            + str(dim)
            + ". The size of "
            + "this dimension in the given input is "
            + str(dim_size)
            + ". The model will "
            + "be exported without the squeeze node. If the model is intended to be used with dynamic "
            + "input shapes, please export with dynamic_axes argument.",
            stacklevel=2,
        )
        return self
    return symbolic_helper._squeeze_helper(g, self, [dim])