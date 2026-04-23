def xlogy(a: TensorLikeType | NumberType, b: TensorLikeType | NumberType):
    torch._check(
        isinstance(a, TensorLike) or isinstance(b, TensorLike),
        lambda: 'Expected either argument a or b to be a Tensor"',
    )

    # Operations like eq and log do not handle scalar values, so we convert them to scalar_tensors.
    if isinstance(b, TensorLike) and isinstance(a, Number):
        # pyrefly: ignore [bad-argument-type]
        a = scalar_tensor(a, dtype=b.dtype, device=b.device)
    elif isinstance(a, TensorLike) and isinstance(b, Number):
        # pyrefly: ignore [bad-argument-type]
        b = scalar_tensor(b, dtype=a.dtype, device=a.device)

    # mypy: expected "Tensor"
    if not isinstance(a, TensorLike):
        raise AssertionError(f"a must be TensorLike, got {type(a)}")
    if not isinstance(b, TensorLike):
        raise AssertionError(f"b must be TensorLike, got {type(b)}")
    rhs = torch.where(torch.eq(a, 0), 0, torch.mul(a, torch.log(b)))
    return torch.where(torch.isnan(b), float("nan"), rhs)