def rmsprop(
    params: list[Tensor],
    grads: list[Tensor],
    square_avgs: list[Tensor],
    grad_avgs: list[Tensor],
    momentum_buffer_list: list[Tensor],
    state_steps: list[Tensor],
    # kwonly args with defaults are not supported by functions compiled with torchscript issue #70627
    # setting this as kwarg for now as functional API is compiled by torch/distributed/optim
    foreach: bool | None = None,
    maximize: bool = False,
    differentiable: bool = False,
    capturable: bool = False,
    has_complex: bool = False,
    *,
    lr: float,
    alpha: float,
    eps: float,
    weight_decay: float,
    momentum: float,
    centered: bool,
) -> None:
    r"""Functional API that performs rmsprop algorithm computation.

    See :class:`~torch.optim.RMSProp` for details.
    """
    # this check is slow during compilation, so we skip it
    # if it's strictly needed we can add this check back in dynamo
    if not torch.compiler.is_compiling() and not all(
        isinstance(t, torch.Tensor) for t in state_steps
    ):
        raise RuntimeError(
            "API has changed, `state_steps` argument must contain a list of singleton tensors"
        )

    if foreach is None:
        _, foreach = _default_to_fused_or_foreach(
            params, differentiable, use_fused=False
        )

    if foreach and torch.jit.is_scripting():
        raise RuntimeError("torch.jit.script not supported with foreach optimizers")

    if foreach and not torch.jit.is_scripting():
        func = _multi_tensor_rmsprop
    else:
        func = _single_tensor_rmsprop

    func(
        params,
        grads,
        square_avgs,
        grad_avgs,
        momentum_buffer_list,
        state_steps,
        lr=lr,
        alpha=alpha,
        eps=eps,
        weight_decay=weight_decay,
        momentum=momentum,
        centered=centered,
        maximize=maximize,
        capturable=capturable,
        differentiable=differentiable,
        has_complex=has_complex,
    )