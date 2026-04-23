def compute_expected_grads(op, args, kwargs, output_process_fn_grad=None, gradcheck_wrapper=None):
    if gradcheck_wrapper is None:
        results = op(*args, **kwargs)
    else:
        results = gradcheck_wrapper(op, *args, **kwargs)

    if output_process_fn_grad is not None:
        results = output_process_fn_grad(results)

    flat_results = pytree.tree_leaves(results)
    flat_results = [r for r in flat_results if isinstance(r, torch.Tensor)]
    flat_diff_results = [r for r in flat_results if r.requires_grad]
    if len(flat_diff_results) <= 0:
        raise AssertionError("Expected len(flat_diff_results) > 0")

    grads = [torch.ones(r.shape, device=r.device, dtype=r.dtype) for r in flat_diff_results]
    leaf_tensors = gather_leaf_tensors(args, kwargs)
    if len(leaf_tensors) <= 0:
        raise AssertionError("Expected len(leaf_tensors) > 0")
    return torch.autograd.grad(flat_diff_results, leaf_tensors,
                               grads, allow_unused=True, retain_graph=True)