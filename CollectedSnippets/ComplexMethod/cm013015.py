def tensor_split(
    g: jit_utils.GraphContext, self, indices_or_sections, dim, _outputs=None
):
    axis = g.op("Constant", value_t=torch.tensor(dim, dtype=torch.long))
    axis = opset11.unsqueeze(g, axis, 0)
    const_1 = g.op("Constant", value_t=torch.tensor(1, dtype=torch.long))

    if symbolic_helper._is_split_static(indices_or_sections, _outputs):
        split_val = symbolic_helper._node_get(indices_or_sections.node(), "value")

        if split_val.dim() > 0:
            start = g.op("Constant", value_t=torch.tensor([0], dtype=torch.long))
            res = []
            if _outputs is None:
                raise AssertionError("_outputs must be non-None")
            for i in range(_outputs - 1):
                end = g.op(
                    "Gather",
                    indices_or_sections,
                    g.op("Constant", value_t=torch.tensor([i], dtype=torch.long)),
                    axis_i=0,
                )
                res.append(g.op("Slice", self, start, end, axis))
                start = end

            end = symbolic_helper._size_helper(g, self, axis)
            res.append(g.op("Slice", self, start, end, axis))
            return res

        split_size = symbolic_helper._get_const(
            indices_or_sections, "i", "indices_or_sections"
        )

        size = symbolic_helper._get_tensor_dim_size(self, dim)
        if size is None:
            if _outputs is not None:
                size = split_size * _outputs
            else:
                raise errors.SymbolicValueError(
                    "Unknown dimension size not supported", self
                )

        min_split_size = size // split_size
        num_splits_one_extra = size % split_size

        splits = num_splits_one_extra * [min_split_size + 1]
        leftover = (split_size - num_splits_one_extra) * [min_split_size]

        splits = g.op(
            "Constant", value_t=torch.tensor(splits + leftover, dtype=torch.long)
        )
        # pyrefly: ignore [bad-argument-type]
        return g.op("Split", self, splits, axis_i=dim, outputs=_outputs)

    if (
        symbolic_helper._is_tensor(indices_or_sections)
        and symbolic_helper._get_tensor_rank(indices_or_sections) == 1
    ):
        loop_len = symbolic_helper._size_helper(
            g, indices_or_sections, g.op("Constant", value_t=torch.tensor(0))
        )
        loop_len = opset11.unsqueeze(g, loop_len, 0)
        loop_condition = g.op("Cast", const_1, to_i=_C_onnx.TensorProtoDataType.BOOL)

        # To make the first slice in the below loop work,
        # we pad a zero to the first position so that it will be the initial start of slice.
        padding_0 = g.op("Constant", value_t=torch.tensor([0], dtype=torch.long))
        indices_or_sections = g.op("Concat", padding_0, indices_or_sections, axis_i=0)

        final_splits = g.op("SequenceEmpty")
        # Loop inputs
        loop, (loop_context,), _ = jit_utils.add_op_with_blocks(
            g, "Loop", loop_len, loop_condition, final_splits, outputs=1, n_blocks=1
        )

        loop_block = loop_context.block
        block_input_iter = utils._add_input_to_block(loop_block)
        cond = utils._add_input_to_block(loop_block)  # noqa: F841
        final_splits = utils._add_input_to_block(loop_block)

        start = loop_context.op(
            "Gather", indices_or_sections, block_input_iter, axis_i=0
        )
        end = loop_context.op(
            "Gather",
            indices_or_sections,
            loop_context.op("Add", block_input_iter, const_1),
            axis_i=0,
        )

        slice = loop_context.op("Slice", self, start, end, axis)
        final_splits = loop_context.op("SequenceInsert", final_splits, slice)

        # Loop outputs
        cond_out = loop_context.op("Identity", loop_condition)
        utils._add_output_to_block(loop_block, cond_out)
        utils._add_output_to_block(loop_block, final_splits)

        loop_out = loop.node().output()
        start = g.op(
            "Gather",
            indices_or_sections,
            g.op("Constant", value_t=torch.tensor(-1, dtype=torch.long)),
            axis_i=0,
        )
        start = opset11.unsqueeze(g, start, 0)
        end = symbolic_helper._size_helper(g, self, axis)

        last_slice = g.op("Slice", self, start, end, axis)

        return g.op("SequenceInsert", loop_out, last_slice)

    else:  # scalar tensor
        dim_size = symbolic_helper._size_helper(g, self, axis)
        min_split_size = g.op("Div", dim_size, indices_or_sections)
        min_split_size_plus_1 = g.op(
            "Add",
            min_split_size,
            const_1,
        )
        num_splits_one_extra = g.op("Mod", dim_size, indices_or_sections)
        splits = g.op("Tile", min_split_size_plus_1, num_splits_one_extra)
        leftover = g.op(
            "Tile",
            min_split_size,
            g.op(
                "Sub",
                opset11.unsqueeze(g, indices_or_sections, 0),
                num_splits_one_extra,
            ),
        )

        splits = g.op("Concat", splits, leftover, axis_i=0)
        if _outputs is None:
            return g.op("SplitToSequence", self, splits, axis_i=dim)
        return g.op("Split", self, splits, axis_i=dim, outputs=_outputs)