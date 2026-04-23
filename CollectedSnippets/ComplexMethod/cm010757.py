def wrap_outputs_maintaining_identity(
    outputs: Any,
    unwrapped_inputs: Any,
    orig_inputs: Any,
    wrap_fn: Callable[..., Any],
    out_dims: Any = NO_OUT_DIMS,
) -> Any:
    flat_unwrapped_inputs = pytree.arg_tree_leaves(*unwrapped_inputs)
    flat_orig_inputs = pytree.arg_tree_leaves(*orig_inputs)

    unwrapped_input_to_orig_input = {
        id(unwrapped): orig
        for unwrapped, orig in zip(flat_unwrapped_inputs, flat_orig_inputs)
    }

    flat_outputs, spec = pytree.tree_flatten(outputs)
    result = []

    out_dims_specified = out_dims != NO_OUT_DIMS

    flat_out_dims = None
    if out_dims_specified:
        flat_out_dims = _broadcast_to_and_flatten(out_dims, spec)
        # _broadcast_to_and_flatten returns None if it is unable to broadcast.
        # TODO: update following link from master to stable once that's out
        if flat_out_dims is None:
            raise RuntimeError(
                f"The autograd.Function's vmap staticmethod returned an "
                f"incompatible (output, out_dims) tuple. "
                f"Expected out_dims={out_dims} "
                f"to be compatible with the structure of `output`. "
                f"out_dims has structure {pytree.tree_flatten(out_dims)[1]} "
                f"but output has structure {spec}. "
                f"For more details, please see "
                f"https://pytorch.org/docs/main/notes/extending.func.html"
            )

    for i, output in enumerate(flat_outputs):
        if not isinstance(output, torch.Tensor):
            result.append(output)
            continue
        if id(output) in unwrapped_input_to_orig_input:
            result.append(unwrapped_input_to_orig_input[id(output)])
            continue
        if out_dims_specified:
            if flat_out_dims is None:
                raise AssertionError(
                    "flat_out_dims must not be None when out_dims is specified"
                )
            result.append(wrap_fn(output, flat_out_dims[i]))
        else:
            result.append(wrap_fn(output))

    return pytree.tree_unflatten(result, spec)