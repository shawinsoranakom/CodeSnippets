def adadelta(
    params: list[Tensor],
    grads: list[Tensor],
    square_avgs: list[Tensor],
    acc_deltas: list[Tensor],
    state_steps: list[Tensor],
    # kwonly args with defaults are not supported by functions compiled with torchscript issue #70627
    # setting this as kwarg for now as functional API is compiled by torch/distributed/optim
    capturable: bool = False,
    foreach: bool | None = None,
    differentiable: bool = False,
    has_complex: bool = False,
    *,
    lr: float,
    rho: float,
    eps: float,
    weight_decay: float,
    maximize: bool,
) -> None:
    r"""Functional API that performs Adadelta algorithm computation.

    See :class:`~torch.optim.Adadelta` for details.
    """

    # this check is slow during compilation, so we skip it
    # if it's strictly needed we can add this check back in dynamo
    if not torch.compiler.is_compiling() and not all(
        isinstance(t, torch.Tensor) for t in state_steps
    ):
        raise RuntimeError(
            "API has changed, `state_steps` argument must contain a list of singleton tensors"
        )

    # We still respect when the user inputs False for foreach.
    if foreach is None:
        _, foreach = _default_to_fused_or_foreach(
            params, differentiable, use_fused=False
        )

    if foreach and torch.jit.is_scripting():
        raise RuntimeError("torch.jit.script not supported with foreach optimizers")

    if foreach and not torch.jit.is_scripting():
        func = _multi_tensor_adadelta
    else:
        func = _single_tensor_adadelta

    func(
        params,
        grads,
        square_avgs,
        acc_deltas,
        state_steps,
        lr=lr,
        rho=rho,
        eps=eps,
        weight_decay=weight_decay,
        maximize=maximize,
        differentiable=differentiable,
        capturable=capturable,
        has_complex=has_complex,
    )