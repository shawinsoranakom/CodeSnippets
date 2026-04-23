def general_cosine(
    M,
    *,
    a: Iterable,
    sym: bool = True,
    dtype: torch.dtype | None = None,
    layout: torch.layout = torch.strided,
    device: torch.device | None = None,
    requires_grad: bool = False,
) -> Tensor:
    if dtype is None:
        dtype = torch.get_default_dtype()

    _window_function_checks("general_cosine", M, dtype, layout)

    if M == 0:
        return torch.empty(
            (0,), dtype=dtype, layout=layout, device=device, requires_grad=requires_grad
        )

    if M == 1:
        return torch.ones(
            (1,), dtype=dtype, layout=layout, device=device, requires_grad=requires_grad
        )

    if not isinstance(a, Iterable):
        raise TypeError("Coefficients must be a list/tuple")

    if not a:
        raise ValueError("Coefficients cannot be empty")

    constant = 2 * torch.pi / (M if not sym else M - 1)

    k = torch.linspace(
        start=0,
        end=(M - 1) * constant,
        steps=M,
        dtype=dtype,
        layout=layout,
        device=device,
        requires_grad=requires_grad,
    )

    a_i = torch.tensor(
        [(-1) ** i * w for i, w in enumerate(a)],
        device=device,
        dtype=dtype,
        requires_grad=requires_grad,
    )
    i = torch.arange(
        a_i.shape[0],
        dtype=a_i.dtype,
        device=a_i.device,
        requires_grad=a_i.requires_grad,
    )
    return (a_i.unsqueeze(-1) * torch.cos(i.unsqueeze(-1) * k)).sum(0)