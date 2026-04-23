def _embedding_bag_helper(
    g: jit_utils.GraphContext,
    embedding_matrix,
    indices,
    offsets,
    scale_grad_by_freq,
    mode,
    sparse,
    per_sample_weights,
    include_last_offset,
    padding_idx,
):
    if scale_grad_by_freq and GLOBALS.export_training:
        return _onnx_unsupported(
            "embedding_bag with scale_grad_by_freq for training mode"
        )
    if padding_idx is not None and padding_idx >= 0:
        raise RuntimeError("embedding_bag with padding_idx")

    loop_condition = g.op("Constant", value_t=torch.tensor(1))
    loop_condition = g.op("Cast", loop_condition, to_i=_C_onnx.TensorProtoDataType.BOOL)
    zero = g.op("Constant", value_t=torch.tensor([0]))

    indices_len = _unsqueeze_helper(
        g,
        _size_helper(g, indices, g.op("Constant", value_t=torch.tensor(0))),
        [0],
    )
    if not include_last_offset:
        offsets = [offsets, indices_len]
        offsets = g.op("Concat", *offsets, axis_i=0)

    # Offsets holds the starting index position of each bag. So we create a list of the indices slices (determined by
    # offsets) and gather those indices in indices_row. Then we use this subset of indices to gather from embeddings.
    # The embeddings output is a loop scan output, so we can avoid creating a sequence and inserting elements in.
    offsets_starts = _slice_helper(
        g, offsets, axes=[0], starts=[0], ends=[sys.maxsize], steps=[1]
    )
    offsets_ends = _slice_helper(
        g, offsets, axes=[0], starts=[1], ends=[sys.maxsize], steps=[1]
    )

    loop_len = _size_helper(g, offsets_ends, g.op("Constant", value_t=torch.tensor(0)))

    loop, (loop_context,), _ = jit_utils.add_op_with_blocks(
        g, "Loop", loop_len, loop_condition, n_blocks=1
    )
    loop_block = loop_context.block

    # FIXME(justinchuby): We need to handle what happens when we call b.op on a node return
    block_input_iter = utils._add_input_to_block(loop_block)
    utils._add_input_to_block(loop_block)

    indices_start = loop_context.op(
        "Gather", offsets_starts, block_input_iter, axis_i=0
    )
    indices_end = loop_context.op("Gather", offsets_ends, block_input_iter, axis_i=0)
    indices_start = _unsqueeze_helper(loop_context, indices_start, [0])
    indices_end = _unsqueeze_helper(loop_context, indices_end, [0])

    indices_row = loop_context.op("Slice", indices, indices_start, indices_end, zero)
    embeddings = loop_context.op("Gather", embedding_matrix, indices_row, axis_i=0)
    if not _is_none(per_sample_weights):
        per_sample_weights_row = loop_context.op(
            "Slice", per_sample_weights, indices_start, indices_end, zero
        )
        per_sample_weights_row = _unsqueeze_helper(
            loop_context, per_sample_weights_row, [1]
        )
        embeddings = loop_context.op("Mul", embeddings, per_sample_weights_row)
    if mode == 0:
        embeddings = _reducesum_helper(
            loop_context, embeddings, axes_i=[0], keepdims_i=0
        )
    elif mode == 1:
        if loop_context.opset < 18:
            embeddings = loop_context.op(
                "ReduceMean", embeddings, axes_i=[0], keepdims_i=0
            )
        else:
            axes = loop_context.op(
                "Constant", value_t=torch.tensor([0], dtype=torch.long)
            )
            embeddings = loop_context.op("ReduceMean", embeddings, axes, keepdims_i=0)
    else:
        if loop_context.opset < 18:
            embeddings = loop_context.op(
                "ReduceMax", embeddings, axes_i=[0], keepdims_i=0
            )
        else:
            axes = loop_context.op(
                "Constant", value_t=torch.tensor([0], dtype=torch.long)
            )
            embeddings = loop_context.op("ReduceMax", embeddings, axes, keepdims_i=0)

    cond_out = loop_context.op(
        "Cast", loop_condition, to_i=_C_onnx.TensorProtoDataType.BOOL
    )
    utils._add_output_to_block(loop_block, cond_out)
    utils._add_output_to_block(loop_block, embeddings)

    # aten::embedding_bag returns a tuple of 4 elements: output, offset2bag, bag_size, max_indices.
    # But the last three outputs are not used in torch.nn.EmbeddingBag or torch.nn.functional.embedding_bag.
    return loop.node().output(), None, None, None