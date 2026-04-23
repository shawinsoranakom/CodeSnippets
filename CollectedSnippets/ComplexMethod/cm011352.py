def _init_optim_state(optim: torch.optim.Optimizer) -> None:
    """
    Initialize optim states by calling the step() with zero grads.
    """
    if optim.state:
        # The optimizer state is initialized.
        return

    # There are some stateless optimizers like SGD. These optimizer will
    # not return in the above condition. So if gradients exist, we should also
    # return. If gradients do not exist, the following initialization should
    # not disturb SGD because the gradients and lr are both zero.
    for param_group in optim.param_groups:
        for param in param_group[_PARAMS]:
            if param.grad is not None:
                return

    for param_group in optim.param_groups:
        for param in param_group[_PARAMS]:
            if param.requires_grad:
                param.grad = torch.zeros_like(param)

    # Some optimizers will update parameters regardless of grads due to lr, so
    # make lr to zero when calling `step()`.
    lrs = []
    for param_group in optim.param_groups:
        if "lr" in param_group:
            lrs.append(param_group["lr"])
            param_group["lr"] = (
                torch.tensor(0.0)
                if isinstance(param_group["lr"], torch.Tensor)
                else 0.0
            )
    optim.step(closure=None)
    # Whether to recover the "lr" should not matter too much as we will
    # restore checkpointing later.
    for param_group in optim.param_groups:
        if "lr" in param_group:
            param_group["lr"] = lrs.pop(0)
    optim.zero_grad(set_to_none=True)