def reference_vmap(op, inputs, in_dims=0, out_dims=0, return_nt=False):
    if isinstance(in_dims, int):
        in_dims = (in_dims,) * len(inputs)
    bdim_sizes = [inp.size(dim) for inp, dim in zip(inputs, in_dims) if dim is not None]
    if not all(bdim_size == bdim_sizes[0] for bdim_size in bdim_sizes):
        raise AssertionError(f"Expected all bdim sizes to be equal, got {bdim_sizes}")
    bdim_size = bdim_sizes[0]
    results = tuple(op(*slice_inputs(inputs, in_dims, i)) for i in range(bdim_size))

    if len(results) == 0:
        raise AssertionError("Expected at least one result")
    op_has_single_return = not isinstance(results[0], tuple)
    if op_has_single_return:
        if not all(isinstance(result, torch.Tensor) for result in results):
            raise AssertionError(
                "Expected all results to be torch.Tensor for single-return op"
            )
        if isinstance(out_dims, int):
            out_dims = (out_dims,) * 1
        if return_nt:
            return torch.nested.nested_tensor(list(results))
        else:
            return torch.stack(results, dim=out_dims[0])

    if not all(isinstance(result, tuple) for result in results):
        raise AssertionError("Expected all results to be tuples")
    num_returns = len(results[0])
    if not all(len(result) == num_returns for result in results):
        raise AssertionError(f"Expected all results to have {num_returns} elements")
    if isinstance(out_dims, int):
        out_dims = (out_dims,) * num_returns
    if return_nt:
        return tuple(
            torch.nested.nested_tensor(list(result_shards))
            for result_shards in zip(*results)
        )
    else:
        return tuple(
            torch.stack(result_shards, out_dim)
            for result_shards, out_dim in zip(zip(*results), out_dims)
        )