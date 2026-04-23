def gaussian_nll_loss(
    input: Tensor,
    target: Tensor,
    var: Tensor | float,
    full: bool = False,
    eps: float = 1e-6,
    reduction: str = "mean",
) -> Tensor:
    r"""Compute the Gaussian negative log likelihood loss.

    See :class:`~torch.nn.GaussianNLLLoss` for details.

    Args:
        input: Expectation of the Gaussian distribution.
        target: Sample from the Gaussian distribution.
        var: Tensor of positive variance(s), one for each of the expectations
            in the input (heteroscedastic), or a single one (homoscedastic),
            or a positive scalar value to be used for all expectations.
        full (bool, optional): Whether to include the constant term in the loss calculation. Default: ``False``.
        eps (float, optional): Value added to var, for stability. Default: 1e-6.
        reduction (str, optional): Specifies the reduction to apply to the output:
            ``'none'`` | ``'mean'`` | ``'sum'``. ``'none'``: no reduction will be applied,
            ``'mean'``: the output is the average of all batch member losses,
            ``'sum'``: the output is the sum of all batch member losses.
            Default: ``'mean'``.
    """
    if has_torch_function_variadic(input, target, var):
        return handle_torch_function(
            gaussian_nll_loss,
            (input, target, var),
            input,
            target,
            var,
            full=full,
            eps=eps,
            reduction=reduction,
        )

    # Entries of var must be non-negative
    if isinstance(var, float):
        if var < 0:
            raise ValueError("var has negative entry/entries")
        var = var * torch.ones_like(input)
    elif torch.any(var < 0):
        raise ValueError("var has negative entry/entries")

    # Check var size
    # If var.size == input.size, the case is heteroscedastic and no further checks are needed.
    # Otherwise:
    if var.size() != input.size():
        # If var is one dimension short of input, but the sizes match otherwise, then this is a homoscedastic case.
        # e.g. input.size = (10, 2, 3), var.size = (10, 2)
        # -> unsqueeze var so that var.shape = (10, 2, 1)
        # this is done so that broadcasting can happen in the loss calculation
        if input.size()[:-1] == var.size():
            var = torch.unsqueeze(var, -1)

        # This checks if the var is broadcastable to the input and there is only one mismatched dimension.
        # This is also a homoscedastic case.
        # e.g. input.size = (10, 2, 3), var.size = (10, 2, 1)
        # or  input.size = (4, 3, 32, 32), var.size = (4, 1, 32, 32)
        elif (
            input.ndim == var.ndim
            and sum(y for x, y in zip(input.size(), var.size(), strict=True) if x != y)
            == 1
        ):  # Heteroscedastic case
            pass

        # If none of the above pass, then the size of var is incorrect.
        else:
            raise ValueError("var is of incorrect size")

    # Check validity of reduction mode
    if reduction != "none" and reduction != "mean" and reduction != "sum":
        raise ValueError(reduction + " is not valid")

    # Clamp for stability
    var = var.clone()
    with torch.no_grad():
        var.clamp_(min=eps)

    # Calculate the loss
    loss = 0.5 * (torch.log(var) + (input - target) ** 2 / var)
    if full:
        loss += 0.5 * math.log(2 * math.pi)

    if reduction == "mean":
        return loss.mean()
    elif reduction == "sum":
        return loss.sum()
    else:
        return loss