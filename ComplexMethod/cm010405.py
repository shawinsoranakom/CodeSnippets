def while_loop_dense(
    cond_fn, body_fn, carried_inputs, additional_inputs, stack_output=False
):
    carried_vals = carried_inputs

    def _validate_cond_output(pred):
        if (
            isinstance(pred, torch.Tensor)
            and pred.size() == torch.Size([])
            and pred.dtype == torch.bool
        ) or isinstance(pred, bool):
            return
        else:
            raise RuntimeError(
                f"cond_fn must return a boolean scalar tensor or a boolean but got {pred}"
            )

    if not isinstance(carried_inputs, (tuple, list)):
        raise RuntimeError(
            f"carried_inputs must be a tuple or list but got {type(carried_inputs)}"
        )

    # Check condition and set up flag
    should_loop = cond_fn(*carried_vals, *additional_inputs)
    _validate_cond_output(should_loop)

    if not should_loop:
        if stack_output:
            return tuple(
                val.unsqueeze(0).clone() if isinstance(val, torch.Tensor) else val
                for val in carried_vals
            )
        else:
            return tuple(
                val.clone() if isinstance(val, torch.Tensor) else val
                for val in carried_vals
            )

    outputs: list[list[torch.Tensor]] = [[] for _ in carried_vals]

    while should_loop:
        out = body_fn(*carried_vals, *additional_inputs)
        if stack_output:
            for i, o in enumerate(out):
                outputs[i].append(o)

        if not isinstance(out, tuple):
            raise AssertionError(f"body_fn should return a tuple but got {type(out)}")
        if len(out) != len(carried_inputs):
            raise AssertionError(
                f"body_fn should return the same number of elements as carried_inputs, got {len(out)} vs {len(carried_inputs)}"
            )
        carried_vals = out

        should_loop = cond_fn(*carried_vals, *additional_inputs)

    if stack_output:
        outs: list[torch.Tensor] = []
        for out in outputs:
            outs.append(torch.stack(out, dim=0))
        return tuple(outs)

    return carried_vals