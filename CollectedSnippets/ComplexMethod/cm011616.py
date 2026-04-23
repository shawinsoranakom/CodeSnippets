def prelu(a: TensorLikeType, weight: TensorLikeType) -> TensorLikeType:
    """
    Reference implementation of torch.nn.functional.prelu
    """
    torch._check(
        isinstance(a, TensorLike),
        lambda: f"prelu: Expected `a` to be tensor, but got: {type(a)}",
    )
    torch._check(
        isinstance(weight, TensorLike),
        lambda: f"prelu: Expected `weight` to be tensor, but got: {type(weight)}",
    )

    if weight.numel() != 1:
        torch._check(a.ndim > 0, lambda: "Not allow zero-dim input tensor.")
        channel_size = a.shape[1] if a.ndim >= 2 else 1
        torch._check(
            weight.numel() == channel_size,
            lambda: f"Mismatch of parameter numbers and input channel size. Found parameter numbers ="
            f" {weight.numel()} and channel size = {channel_size}.",
        )

    torch._check(
        weight.ndim == 0 or weight.ndim == 1,
        lambda: f"prelu: Expected `weight` to be a scalar or 1D tensor, but got: "
        f"ndim = {weight.ndim}",
    )
    if a.ndim == 0:
        weight = weight[0] if weight.ndim == 1 else weight
    else:
        weight = prims.broadcast_in_dim(
            weight, a.shape, () if weight.ndim == 0 else (0 if a.ndim == 1 else 1,)
        )

    return torch.where(a > 0, a, a * weight)