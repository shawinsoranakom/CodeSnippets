def loop(op, in_dims, out_dim, batch_size, *batched_args, **kwarg_values):
    outs = []
    out_spec = None
    for idx in range(batch_size):
        flat_args, args_spec = pytree.tree_flatten(batched_args)
        flat_dims, dims_spec = pytree.tree_flatten(in_dims)
        if args_spec != dims_spec:
            raise AssertionError(f"args_spec {args_spec} != dims_spec {dims_spec}")
        new_args = [
            a.select(in_dim, idx) if in_dim is not None else a
            for a, in_dim in zip(flat_args, flat_dims)
        ]
        out = op(*pytree.tree_unflatten(new_args, args_spec), **kwarg_values)
        flat_out, out_spec = pytree.tree_flatten(out)
        outs.append(flat_out)

    # use the same out_dim for all outputs
    if isinstance(out_dim, int):
        flat_out_dim = [out_dim for _ in flat_out]
    else:
        flat_out_dim, _ = pytree.tree_flatten(out_dim)

    outs = zip(*outs)

    result = []
    for i, out_lst in enumerate(outs):
        if flat_out_dim[i] is not None:
            if not all(isinstance(x, torch.Tensor) for x in out_lst):
                raise ValueError(
                    f"vmap `{op}` must only return "
                    "Tensors. Did you mean to set out_dims= to None for output?"
                )
            result.append(torch.stack(out_lst))
        else:
            # not batched over, result should be the same for all batches
            result.append(out_lst[0])
    return pytree.tree_unflatten(result, out_spec)