def loop2(
    op,
    in_dims1,
    in_dims2,
    out_dim1,
    out_dim2,
    batch_size1,
    batch_size2,
    *batched_args,
    **kwarg_values,
):
    outs = []
    flat_args, args_spec = pytree.tree_flatten(batched_args)
    flat_dims1, dims_spec1 = pytree.tree_flatten(in_dims1)
    flat_dims2, dims_spec2 = pytree.tree_flatten(in_dims2)
    if args_spec != dims_spec1:
        raise AssertionError(f"args_spec {args_spec} != dims_spec1 {dims_spec1}")
    if args_spec != dims_spec2:
        raise AssertionError(f"args_spec {args_spec} != dims_spec2 {dims_spec2}")
    if len(flat_dims1) != len(flat_dims2):
        raise AssertionError(
            f"len(flat_dims1) {len(flat_dims1)} != len(flat_dims2) {len(flat_dims2)}"
        )
    for idx1 in range(batch_size1):
        out_split = []
        arg_split = [
            a.select(in_dim1, idx1) if in_dim1 is not None else a
            for a, in_dim1 in zip(flat_args, flat_dims1)
        ]
        for idx2 in range(batch_size2):
            new_args = [
                a.select(in_dim, idx2) if in_dim is not None else a
                for a, in_dim in zip(arg_split, flat_dims2)
            ]
            out = op(*pytree.tree_unflatten(new_args, args_spec), **kwarg_values)
            out_split.append(out)
        outs.append(out_split)

    loop_out = []
    for out_split in outs:
        if isinstance(out_split[0], torch.Tensor):
            loop_out.append(torch.stack(out_split, out_dim1))
        else:
            new_out = []
            for idx in range(len(out_split[0])):
                new_out.append(torch.stack([i[idx] for i in out_split], out_dim1))
            loop_out.append(new_out)

    new_out = []
    if isinstance(loop_out, torch.Tensor):
        new_out = torch.stack(loop_out, out_dim2)
    else:
        for idx in range(len(loop_out[0])):
            new_out.append(torch.stack([i[idx] for i in loop_out], out_dim2))
    return new_out