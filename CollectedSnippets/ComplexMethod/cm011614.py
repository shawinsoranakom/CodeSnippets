def nll_loss(
    input: TensorLikeType,
    target: TensorLikeType,
    weight: TensorLikeType | None = None,
    size_average: bool | None = None,
    ignore_index: int = -100,
    reduce: bool | None = None,
    reduction: str = "mean",
) -> TensorLikeType:
    """
    Reference implementation of torch.nn.functional.nll_loss
    """
    torch._check(
        input.ndim > 0,
        lambda: f"Expected input tensor to have 1 or more dimensions (got {input.ndim})",
    )

    # TODO: raise exception instead of converting value
    # msg = "size_average and reduce args are deprecated, please use reduction argument."
    # Convert these options for consistency with the eager mode
    if size_average is not None or reduce is not None:
        reduction = _get_string_reduction_arg(size_average=size_average, reduce=reduce)

    # The expected behavior when the target and input have zero elements:
    #   reduction = 'none' --- tensor([])
    #   reduction = 'sum'  --- tensor(0.)
    #   reduction = 'mean' --- tensor(nan)
    # Mean reduction on empty tensors produces NaN. See the discussion in
    # https://github.com/pytorch/pytorch/pull/64572#issuecomment-926504162
    if input.numel() == 0 and target.numel() == 0:
        if reduction == "none":
            return torch.zeros_like(target)
        elif reduction == "sum":
            return torch.empty_like(target)
        else:
            return torch.full_like(target, float("nan"))

    # The _nll_loss_nd helper function handles the most common cases.
    # ndim == 1 (Single Example)
    #   => Batch Size: 1, Input: (C), Target: ()
    # ndim == 2 (k = 1)
    #   => Batch Size: N, Input: (N, C), Target: (N)
    # ndim == 3 (k > 1)
    #   => Batch Size: N, Input: (N, C, K), Target: (N, K)
    if input.ndim <= 3:
        return _nll_loss_nd(input, target, weight, reduction, ignore_index)

    # For ndim > 3, we reshape the input and target to 3-D case.
    # Input (N batch-size, C classes, k-dimensions)
    # Target (N batch-size, k-dimensions)
    torch._check(
        input.ndim > 0 and target.ndim > 0 and target.shape[1:] == input.shape[2:],
        lambda: (
            "Expected input and target to both have ndim > 0 and "
            "target.shape[1:] == input.shape[2:], but got "
            f"target.shape {target.shape} and input.shape {input.shape}"
        ),
    )

    batch_size = input.shape[0]
    num_classes = input.shape[1]
    out_size = [batch_size] + list(target.shape[1:])

    input = torch.reshape(input, [batch_size, num_classes, -1])
    target = torch.reshape(target, [batch_size, -1])
    if reduction != "none":
        return _nll_loss_nd(input, target, weight, reduction, ignore_index)
    else:
        result = _nll_loss_nd(input, target, weight, reduction, ignore_index)
        # reshape flattened inner-dim to original k-dimensions
        return torch.reshape(result, out_size)