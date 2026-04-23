def normal(
    mean=0,
    std=1,
    size=None,
    *,
    generator=None,
    dtype=None,
    layout=None,
    device=None,
    pin_memory=None,
):
    if layout is not None and layout != torch.strided:
        raise AssertionError(f"layout must be None or torch.strided, got {layout}")

    if not isinstance(std, TensorLike):
        torch._check(
            std >= 0, lambda: f"normal expects std >= 0.0, but found std {std}"
        )

    if size is None:
        tensors = tuple(t for t in (mean, std) if isinstance(t, TensorLike))
        torch._check(
            len(tensors) > 0,
            lambda: "normal expects that either mean or std is a tensor, or size is defined",
        )
        torch._check(
            layout is None and pin_memory is None,
            lambda: "Cannot pass layout, or pin_memory without size",
        )

        size = _broadcast_shapes(*(t.shape for t in tensors))
        dtype = tensors[0].dtype
        device = tensors[0].device
    else:
        torch._check(
            not isinstance(mean, TensorLike) and not isinstance(std, TensorLike),
            lambda: "normal expects mean and std to be scalars when size is defined",
        )
        dtype = torch.get_default_dtype() if dtype is None else dtype
        device = torch.device("cpu") if device is None else device

    normal_samples = prims.normal(
        size,
        mean=0.0,
        std=1.0,
        dtype=dtype,
        device=device,
        requires_grad=False,
        generator=generator,
    )
    return std * normal_samples + mean