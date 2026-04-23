def embedding_bag(
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
        return symbolic_helper._onnx_unsupported(
            "embedding_bag with scale_grad_by_freq for training mode"
        )
    if padding_idx is not None and padding_idx >= 0:
        raise RuntimeError("embedding_bag with padding_idx")

    warnings.warn(
        "Export of embedding_bag with dynamic input/offsets shape is not supported in opset 10. "
        "Please use opset 11 or higher to export model for dynamic input shape.'",
        stacklevel=2,
    )
    offsets_dim_0 = symbolic_helper._get_tensor_dim_size(offsets, 0)
    if offsets_dim_0 is not None:
        if include_last_offset:
            offset_len = offsets_dim_0 - 1
            offsets_extended = offsets
        else:
            offset_len = offsets_dim_0
            offsets_extended = [
                offsets,
                g.op("Constant", value_t=torch.tensor([sys.maxsize])),
            ]
            offsets_extended = g.op("Concat", *offsets_extended, axis_i=0)
        list_ = []
        for i in range(offset_len):
            start_ = symbolic_helper._unsqueeze_helper(
                g,
                opset9.select(g, offsets_extended, torch.tensor(0), torch.tensor(i)),
                [0],
            )
            end_ = symbolic_helper._unsqueeze_helper(
                g,
                opset9.select(
                    g, offsets_extended, torch.tensor(0), torch.tensor(i + 1)
                ),
                [0],
            )
            axes_ = g.op("Constant", value_t=torch.tensor([0]))
            indices_row = g.op("Slice", indices, start_, end_, axes_)

            embeddings = g.op("Gather", embedding_matrix, indices_row)
            if not symbolic_helper._is_none(per_sample_weights):
                per_sample_weights_row = g.op(
                    "Slice", per_sample_weights, start_, end_, axes_
                )
                per_sample_weights_row = symbolic_helper._unsqueeze_helper(
                    g, per_sample_weights_row, [1]
                )
                embeddings = g.op("Mul", embeddings, per_sample_weights_row)
            if mode == 0:
                embeddings = symbolic_helper._reducesum_helper(
                    g, embeddings, axes_i=[0], keepdims_i=0
                )
            elif mode == 1:
                embeddings = g.op("ReduceMean", embeddings, axes_i=[0], keepdims_i=0)
            else:
                embeddings = g.op("ReduceMax", embeddings, axes_i=[0], keepdims_i=0)

            embeddings = symbolic_helper._unsqueeze_helper(g, embeddings, [0])
            list_.append(embeddings)

        output = g.op("Concat", *list_, axis_i=0)
        # aten::embedding_bag returns a tuple of 4 elements: output, offset2bag, bag_size, max_indices.
        # But the last three outputs are not used in torch.nn.EmbeddingBag or torch.nn.functional.embedding_bag.
        return output, None, None, None
    else:
        return symbolic_helper._onnx_unsupported(
            "embedding_bag with unknown shape of offsets for opset 10 is not supported. "
            "please use opset 11 or higher."
        )