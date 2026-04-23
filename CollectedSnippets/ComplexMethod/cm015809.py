def _inductor_extra_samples(op_name, device, dtype, requires_grad):
    """Extra sample inputs for inductor-specific coverage.

    These exercise dynamo decomposition paths (e.g. tensor value/alpha triggering
    fma) that the shared opinfo samples don't cover.
    """
    from torch.testing._internal.common_methods_invocations import (
        make_tensor,
        S,
        SampleInput,
    )

    make_arg = partial(
        make_tensor, device=device, dtype=dtype, requires_grad=requires_grad
    )

    if op_name in ("addcmul", "addcdiv") and (
        dtype.is_floating_point or dtype.is_complex
    ):
        # Tensor value
        args = tuple(
            make_arg(shape, exclude_zero=True) for shape in ((S, S), (S, S), (S, S))
        )
        tensor_value = make_arg((), requires_grad=False)
        return [SampleInput(*args, value=tensor_value)]

    if op_name == "add" and (dtype.is_floating_point or dtype.is_complex):
        # Tensor alpha
        lhs = make_arg((S, S))
        rhs = make_arg((S, S))
        tensor_alpha = make_arg((), requires_grad=False)
        return [SampleInput(lhs, args=(rhs,), kwargs={"alpha": tensor_alpha})]

    return []