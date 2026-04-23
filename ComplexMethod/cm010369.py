def cond_batch_rule(interpreter, pred, true_fn, false_fn, inputs):
    if not isinstance(inputs, (list, tuple)):
        raise AssertionError(
            f"Cond inputs must be a list or tuple of tensors, got {type(inputs)}"
        )
    if not all(isinstance(i, torch.Tensor) for i in inputs):
        raise AssertionError(
            f"Cond inputs must be a list of tensors, got {[type(i) for i in inputs]}"
        )

    pred_is_batched = isinstance(pred, torch.Tensor) and is_batchedtensor(pred)
    pred_ = get_unwrapped(pred) if pred_is_batched else pred

    # unbatched tensors are not vmapped
    tensors, in_dims = zip(
        *[
            (get_unwrapped(t), maybe_get_bdim(t)) if is_batchedtensor(t) else (t, None)
            for t in inputs
        ]
    )

    if pred_is_batched:
        # prepend "pred" and vmap everything
        tensors = (pred_,) + tensors
        in_dims = (0,) + in_dims

        def fn(p, *args):
            t = true_fn(*args)
            f = false_fn(*args)
            return torch.where(p, t[0], f[0])

        with interpreter.lower():
            result = torch.vmap(fn, in_dims=in_dims)(*tensors)

    else:
        # predicate is known at this stage and it is a boolean expression or a
        # tensor with one element.
        true_fn = torch.vmap(true_fn, in_dims=in_dims)
        false_fn = torch.vmap(false_fn, in_dims=in_dims)

        with interpreter.lower():
            result = cond_op(pred, true_fn, false_fn, tensors)

    if not isinstance(result, tuple):
        result = (result,)
    lvl = interpreter.level()
    return tuple(_add_batch_dim(r, 0, lvl) for r in result)