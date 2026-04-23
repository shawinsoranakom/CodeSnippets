def repeat_interleave(
    g: jit_utils.GraphContext, self, repeats, dim=None, output_size=None
):
    repeats_dim = symbolic_helper._get_tensor_rank(repeats)
    repeats_sizes = symbolic_helper._get_tensor_sizes(repeats)
    input_sizes = symbolic_helper._get_tensor_sizes(self)
    if repeats_dim is None:
        raise errors.SymbolicValueError(
            "Unsupported: ONNX export of repeat_interleave for unknown repeats rank.",
            self,
        )
    if repeats_sizes is None:
        raise errors.SymbolicValueError(
            "Unsupported: ONNX export of repeat_interleave for unknown repeats size.",
            self,
        )
    if input_sizes is None:
        raise errors.SymbolicValueError(
            "Unsupported: ONNX export of repeat_interleave for unknown input size.",
            self,
        )

    final_dim = dim
    # if dim is None flatten
    # By default, use the flattened input array, and return a flat output array
    if symbolic_helper._is_none(dim):
        self = symbolic_helper._reshape_helper(
            g, self, g.op("Constant", value_t=torch.tensor([-1]))
        )
        dim = torch.tensor(0, dtype=torch.int64)
    else:
        dim = symbolic_helper._maybe_get_scalar(dim)

    # Handle cases where dim is negative
    if dim < 0:
        dim += len(input_sizes)

    output_sizes = input_sizes.copy()
    for idx, input_size in enumerate(input_sizes):
        if input_size is None:
            output_sizes[idx], input_sizes[idx] = 0, -1

    # Check if all indices should be repeated the same number of times.
    if repeats_dim == 0 or (repeats_dim == 1 and repeats_sizes[0] == 1):
        return symbolic_helper._repeat_interleave_single_value_repeat_helper(
            g, self, repeats, dim
        )

    cond_dynamic_repeats = repeats_dim == 1 and repeats_sizes[0] is None
    # If input size is dynamic or repeats vector is dynamic
    if output_sizes[dim] == 0 or cond_dynamic_repeats:
        reps = symbolic_helper._size_helper(g, self, dim)
        reps = opset11.unsqueeze(g, reps, 0)

        # Check if repeats is dynamic
        # As repeats is dynamic, we use a where node as a substitute for the if statement
        # If repests_dim = 1, expand repeats otherwise use original tensor
        if cond_dynamic_repeats:
            repeat_dim = symbolic_helper._size_helper(
                g, repeats, g.op("Constant", value_t=torch.LongTensor([0]))
            )
            repeat_cond = g.op(
                "Equal", repeat_dim, g.op("Constant", value_t=torch.LongTensor([1]))
            )
            repeats = where(g, repeat_cond, g.op("Expand", repeats, reps), repeats)
    # There are cases when the repeats are 1-d tensor with multiple repeats, but dim
    # provided along one of the dynamic axes provided. A simple example would be
    # input.shape -> [1, 1, *] where * represents the dynamic axes, and dim = 2
    # Now, repeat interleaving can be performed in pytorch when the value of * matches
    # with the number of elements in repeat, for example if * -> 2, number of repeats
    # should be 2 as well.
    else:
        return opset9.repeat_interleave(g, self, repeats, final_dim)

    reps_like = g.op(
        "ConstantOfShape",
        g.op("Shape", repeats),
        value_t=torch.tensor([1], dtype=torch.long),
    )
    r_splits = split(g, repeats, reps_like, 0)
    i_splits = split(g, self, reps_like, dim)

    output_sizes[dim], input_sizes[dim] = -1, 1

    # Create a loop to iterate over each value along the dimension
    # and perform individual interleaving using the repeats tensor
    # Loop is of the following pattern
    # input (trip_count, cond)
    #   int trip_count = ...;
    #   bool cond = ...;
    #   for (int i=0; i < trip_count && cond; ++i) {
    #     cond = ...;
    #   }

    # Loop conditions
    loop_condition = g.op("Constant", value_t=torch.tensor(1))
    loop_condition = g.op("Cast", loop_condition, to_i=_C_onnx.TensorProtoDataType.BOOL)
    loop_len = reps

    # Create an empty sequence to store final expansions
    final_splits = g.op("SequenceEmpty")

    # Loop inputs
    loop, (loop_context,), _ = jit_utils.add_op_with_blocks(
        g, "Loop", loop_len, loop_condition, final_splits, n_blocks=1
    )

    loop_block = loop_context.block
    block_input_iter = utils._add_input_to_block(loop_block)
    cond = utils._add_input_to_block(loop_block)  # noqa: F841
    final_splits = utils._add_input_to_block(loop_block)

    r_split = loop_context.op("SequenceAt", r_splits, block_input_iter)
    i_split = loop_context.op("SequenceAt", i_splits, block_input_iter)

    i_split = opset11.unsqueeze(loop_context, i_split, dim + 1)
    r_concat = [
        loop_context.op("Constant", value_t=torch.LongTensor(input_sizes[: dim + 1])),
        r_split,
        loop_context.op("Constant", value_t=torch.LongTensor(input_sizes[dim + 1 :])),
    ]
    r_concat = loop_context.op("Concat", *r_concat, axis_i=0)
    i_split = opset9.expand(loop_context, i_split, r_concat, None)
    i_split = symbolic_helper._reshape_helper(
        loop_context, i_split, g.op("Constant", value_t=torch.LongTensor(output_sizes))
    )
    final_splits = loop_context.op("SequenceInsert", final_splits, i_split)

    # Loop outputs
    cond_out = loop_context.op(
        "Cast", loop_condition, to_i=_C_onnx.TensorProtoDataType.BOOL
    )
    utils._add_output_to_block(loop_block, cond_out)
    utils._add_output_to_block(loop_block, final_splits)

    loop_out = loop.node().output()
    loop_out = g.op("ConcatFromSequence", loop_out, axis_i=dim)
    return loop_out