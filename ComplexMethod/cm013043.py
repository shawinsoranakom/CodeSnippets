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

    input_sizes_temp = input_sizes.copy()
    for idx, input_size in enumerate(input_sizes):
        if input_size is None:
            input_sizes[idx], input_sizes_temp[idx] = 0, -1

    # Cases where repeats is an int or single value tensor
    if repeats_dim == 0 or (repeats_dim == 1 and repeats_sizes[0] == 1):
        if input_sizes[dim] == 0:
            return symbolic_helper._onnx_opset_unsupported_detailed(
                "repeat_interleave",
                9,
                13,
                "Unsupported along dimension with unknown input size",
                self,
            )
        return symbolic_helper._repeat_interleave_single_value_repeat_helper(
            g, self, repeats, dim
        )

    # Cases where repeats is a 1 dim Tensor
    elif repeats_dim == 1:
        if input_sizes[dim] == 0:
            return symbolic_helper._onnx_opset_unsupported_detailed(
                "repeat_interleave",
                9,
                13,
                "Unsupported along dimension with unknown input size",
                self,
            )
        if repeats_sizes[0] is None:
            return symbolic_helper._onnx_opset_unsupported_detailed(
                "repeat_interleave",
                9,
                13,
                "Unsupported for cases with dynamic repeats",
                self,
            )
        if repeats_sizes[0] != input_sizes[dim]:
            raise AssertionError("repeats must have the same size as input along dim")
        reps = repeats_sizes[0]
    else:
        raise errors.SymbolicValueError("repeats must be 0-dim or 1-dim tensor", self)

    final_splits = []
    r_splits = symbolic_helper._repeat_interleave_split_helper(g, repeats, reps, 0)
    i_splits = symbolic_helper._repeat_interleave_split_helper(g, self, reps, dim)
    input_sizes[dim], input_sizes_temp[dim] = -1, 1
    for idx, r_split in enumerate(r_splits):
        i_split = unsqueeze(g, i_splits[idx], dim + 1)
        r_concat = [
            g.op("Constant", value_t=torch.LongTensor(input_sizes_temp[: dim + 1])),
            r_split,
            g.op("Constant", value_t=torch.LongTensor(input_sizes_temp[dim + 1 :])),
        ]
        r_concat = g.op("Concat", *r_concat, axis_i=0)
        i_split = expand(g, i_split, r_concat, None)
        i_split = symbolic_helper._reshape_helper(
            g,
            i_split,
            g.op("Constant", value_t=torch.LongTensor(input_sizes)),
            allowzero=0,
        )
        final_splits.append(i_split)
    return g.op("Concat", *final_splits, axis_i=dim)