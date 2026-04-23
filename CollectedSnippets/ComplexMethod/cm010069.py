def meta_linspace_logspace(
    start,
    end,
    steps,
    base=None,
    dtype=None,
    device=None,
    layout=torch.strided,
    pin_memory=False,
    requires_grad=False,
):
    if isinstance(start, torch.Tensor):
        torch._check(
            start.dim() == 0,
            lambda: "linspace only supports 0-dimensional start and end tensors",
        )
    if isinstance(end, torch.Tensor):
        torch._check(
            end.dim() == 0,
            lambda: "linspace only supports 0-dimensional start and end tensors",
        )

    if any(isinstance(arg, complex) for arg in (start, end, steps)):
        default_complex_dtype = utils.corresponding_complex_dtype(
            torch.get_default_dtype()
        )
        if dtype is None:
            dtype = default_complex_dtype
        else:
            torch._check(
                utils.is_complex_dtype(dtype),
                lambda: f"linspace(): inferred dtype {default_complex_dtype} can't be safely cast to passed dtype {dtype}",
            )
    else:
        dtype = dtype or torch.get_default_dtype()
    if not isinstance(dtype, torch.dtype):
        raise AssertionError(f"dtype must be torch.dtype, got {type(dtype)}")

    # steps does not participate in the computation of the dtype
    torch._check_type(
        isinstance(steps, IntLike),
        lambda: f"received an invalid combination of arguments - got \
({type(start).__name__}, {type(end).__name__}, {type(steps).__name__})",
    )
    if not isinstance(steps, IntLike):
        raise AssertionError(f"steps must be IntLike, got {type(steps)}")
    torch._check(steps >= 0, lambda: "number of steps must be non-negative")

    return torch.empty(
        (steps,),  # type: ignore[arg-type]
        dtype=dtype,
        layout=layout,
        device="meta",
        pin_memory=pin_memory,
        requires_grad=requires_grad,
    )