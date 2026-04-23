def multi_margin_loss(
    input: Tensor,
    target: Tensor,
    p: NumberType = 1,
    margin: NumberType = 1,
    weight: Tensor | None = None,
    reduction: int = Reduction.MEAN.value,
) -> Tensor:
    input = torch.atleast_2d(input)
    target = torch.atleast_1d(target)
    nframe = input.shape[0]
    dim = input.shape[1]
    torch._check(p == 1 or p == 2, lambda: "only p == 1 and p == 2 supported")
    torch._check(
        input.ndim == 2 and dim != 0,
        lambda: f"Expected non-empty vector or matrix with optional 0-dim batch size, but got: {input.shape}",
    )
    torch._check(
        target.ndim == 1 and target.numel() == nframe,
        lambda: f"inconsistent target size, expected {nframe} but got {target.shape}",
    )
    if weight is not None:
        weight = torch.atleast_1d(weight)
        torch._check(
            weight.ndim == 1 and weight.numel() == dim,  # type: ignore[union-attr]
            lambda: f"inconsistent weight size, expected {dim} but got {weight.shape}",  # type: ignore[union-attr]
        )
    target = target.unsqueeze(1)
    u = torch.gather(input, dim=1, index=target)
    z = margin - u + input
    z = z.clamp_min(0)
    z = z if p == 1 else z * z
    if weight is not None:
        z = z * weight[target]
    idx = torch.arange(dim, device=input.device)
    z = torch.where(idx != target, z, 0)
    if reduction == Reduction.MEAN.value:
        return z.mean()
    elif reduction == Reduction.SUM.value:
        return z.sum() / z.shape[1]
    else:
        return z.mean(dim=1)