def filter_empty_gradients(grads_and_vars):
    """Filter out `(grad, var)` pairs that have a gradient equal to `None`."""
    grads_and_vars = tuple(grads_and_vars)
    if not grads_and_vars:
        return grads_and_vars

    filtered = []
    vars_with_empty_grads = []
    for grad, var in grads_and_vars:
        if grad is None:
            vars_with_empty_grads.append(var)
        else:
            filtered.append((grad, var))
    filtered = tuple(filtered)

    if not filtered:
        variable = ([v.name for _, v in grads_and_vars],)
        raise ValueError(
            f"No gradients provided for any variable: {variable}. "
            f"Provided `grads_and_vars` is {grads_and_vars}."
        )
    if vars_with_empty_grads:
        warnings.warn(
            "Gradients do not exist for variables %s when minimizing the "
            "loss. If you're using `model.compile()`, did you forget to "
            "provide a `loss` argument?",
            ([v.name for v in vars_with_empty_grads]),
        )
    return filtered