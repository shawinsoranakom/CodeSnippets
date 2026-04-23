def exponential(
    M: int,
    *,
    center: float | None = None,
    tau: float = 1.0,
    sym: bool = True,
    dtype: torch.dtype | None = None,
    layout: torch.layout = torch.strided,
    device: torch.device | None = None,
    requires_grad: bool = False,
) -> Tensor:
    if dtype is None:
        dtype = torch.get_default_dtype()

    _window_function_checks("exponential", M, dtype, layout)

    if tau <= 0:
        raise ValueError(f"Tau must be positive, got: {tau} instead.")

    if sym and center is not None:
        raise ValueError("Center must be None for symmetric windows")

    if M == 0:
        return torch.empty(
            (0,), dtype=dtype, layout=layout, device=device, requires_grad=requires_grad
        )

    if center is None:
        center = (M if not sym and M > 1 else M - 1) / 2.0

    constant = 1 / tau

    k = torch.linspace(
        start=-center * constant,
        end=(-center + (M - 1)) * constant,
        steps=M,
        dtype=dtype,
        layout=layout,
        device=device,
        requires_grad=requires_grad,
    )

    return torch.exp(-torch.abs(k))