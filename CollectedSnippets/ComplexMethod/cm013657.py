def l1_loss(
    input: Tensor,
    target: Tensor,
    size_average: bool | None = None,
    reduce: bool | None = None,
    reduction: str = "mean",
    weight: Tensor | None = None,
) -> Tensor:
    r"""Compute the L1 loss, with optional weighting.

    Function that takes the mean element-wise absolute value difference.

    See :class:`~torch.nn.L1Loss` for details.

    Args:
        input (Tensor): Predicted values.
        target (Tensor): Ground truth values.
        size_average (bool, optional): Deprecated (see :attr:`reduction`).
        reduce (bool, optional): Deprecated (see :attr:`reduction`).
        reduction (str, optional): Specifies the reduction to apply to the output:
                                   'none' | 'mean' | 'sum'. 'mean': the mean of the output is taken.
                                   'sum': the output will be summed. 'none': no reduction will be applied.
                                   Default: 'mean'.
        weight (Tensor, optional): Weights for each sample. Default: None.

    Returns:
        Tensor: L1 loss (optionally weighted).
    """
    if has_torch_function_variadic(input, target):
        return handle_torch_function(
            l1_loss,
            (input, target, weight),
            input,
            target,
            size_average=size_average,
            reduce=reduce,
            reduction=reduction,
        )
    if target.size() != input.size():
        warnings.warn(
            f"Using a target size ({target.size()}) that is different to the input size ({input.size()}). "
            "This will likely lead to incorrect results due to broadcasting. "
            "Please ensure they have the same size.",
            stacklevel=2,
        )
    if size_average is not None or reduce is not None:
        reduction = _Reduction.legacy_get_string(size_average, reduce)

    expanded_input, expanded_target = torch.broadcast_tensors(input, target)

    if weight is not None:
        if weight.size() != input.size():
            raise ValueError("Weights and input must have the same size.")

        absolute_errors = torch.abs(expanded_input - expanded_target)
        weighted_absolute_errors = absolute_errors * weight

        if reduction == "none":
            return weighted_absolute_errors
        elif reduction == "sum":
            return torch.sum(weighted_absolute_errors)
        elif reduction == "mean":
            return torch.sum(weighted_absolute_errors) / torch.sum(weight)
        else:
            raise ValueError(
                f"Invalid reduction mode: {reduction}. Expected one of 'none', 'mean', 'sum'."
            )
    else:
        return torch._C._nn.l1_loss(
            expanded_input,
            expanded_target,
            # pyrefly: ignore [bad-argument-type]
            _Reduction.get_enum(reduction),
        )