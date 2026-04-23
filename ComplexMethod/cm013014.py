def split(g: jit_utils.GraphContext, self, split_size_or_sizes, dim, _outputs=None):
    if not symbolic_helper._is_split_static(split_size_or_sizes, _outputs):
        split_out = g.op("SplitToSequence", self, split_size_or_sizes, axis_i=dim)
        if _outputs is None:
            return split_out
        # Convert to multiple slice nodes iff number of splits and number of outputs are statically known.
        if (
            symbolic_helper._is_packed_list(split_size_or_sizes)
            and len(symbolic_helper._unpack_list(split_size_or_sizes)) == _outputs
        ):
            split_sizes = [
                symbolic_helper._unsqueeze_helper(g, v, [0])
                for v in symbolic_helper._unpack_list(split_size_or_sizes)
            ]

            start = g.op("Constant", value_t=torch.tensor([0], dtype=torch.long))
            axis = g.op("Constant", value_t=torch.tensor([dim], dtype=torch.long))
            res = []
            for i in range(_outputs):
                end = g.op(
                    "Add", start, split_sizes[i]
                )  # split_sizes is a list of same length as _outputs
                res.append(g.op("Slice", self, start, end, axis))
                start = end
            return res
        return [
            g.op(
                "SequenceAt",
                split_out,
                g.op("Constant", value_t=torch.tensor([i], dtype=torch.long)),
            )
            for i in range(_outputs)
        ]

    split_val = symbolic_helper._node_get(split_size_or_sizes.node(), "value")
    if split_val.dim() > 0:
        # pyrefly: ignore [bad-argument-type]
        return g.op("Split", self, split_size_or_sizes, axis_i=dim, outputs=_outputs)
    split_size = symbolic_helper._get_const(split_size_or_sizes, "i", "split_size")

    size = symbolic_helper._get_tensor_dim_size(self, dim)
    if size is None:
        if _outputs is not None:
            size = split_size * _outputs
        else:
            raise errors.SymbolicValueError(
                "Unknown dimension size not supported", self
            )
    splits = [split_size] * (size // split_size)
    leftover = size % split_size
    if leftover:
        splits.append(leftover)
    splits = g.op("Constant", value_t=torch.tensor(splits))
    # pyrefly: ignore [bad-argument-type]
    return g.op("Split", self, splits, axis_i=dim, outputs=_outputs)