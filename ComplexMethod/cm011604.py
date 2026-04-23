def logspace(
    start: NumberType | TensorLikeType,
    end: NumberType | TensorLikeType,
    steps: NumberType,
    base: NumberType = 10,
    *,
    dtype: torch.dtype | None = None,
    device: DeviceLikeType | None = None,
    layout: torch.layout = torch.strided,
    pin_memory: bool = False,
    requires_grad: bool = False,
) -> TensorLikeType:
    if dtype is None:
        dtype = torch.get_default_dtype()

    # NB: NumPy doesn't have this cast
    if prims.utils.is_integer_dtype(dtype):
        if isinstance(start, FloatLike):
            start = sym_int(start)
        elif isinstance(start, TensorLikeType):
            torch._check(
                start.dim() == 0,
                lambda: "logspace only supports 0-dimensional start and end tensors",
            )
            start = _maybe_convert_to_dtype(start, dtype)
        if isinstance(end, FloatLike):
            end = sym_int(end)
        elif isinstance(end, TensorLikeType):
            torch._check(
                end.dim() == 0,
                lambda: "logspace only supports 0-dimensional start and end tensors",
            )
            end = _maybe_convert_to_dtype(end, dtype)

    if builtins.any(isinstance(arg, complex) for arg in (start, end, steps)):
        default_complex_dtype = utils.corresponding_complex_dtype(
            torch.get_default_dtype()
        )
        dtype = default_complex_dtype
        _dtype = None  # torch.linspace will update the correct dtype
    else:
        _dtype = torch.float64

    if isinstance(base, complex):
        raise AssertionError(f"base must not be complex, got {type(base)}")  # for mypy
    if base < 0:
        raise NotImplementedError
    ret = torch.linspace(  # type: ignore[misc]
        start,  # type: ignore[arg-type]
        end,  # type: ignore[arg-type]
        steps,  # type: ignore[arg-type]
        dtype=_dtype,
        layout=layout,
        device=device,
        pin_memory=pin_memory,
        requires_grad=requires_grad,
    )
    return _maybe_convert_to_dtype(torch.pow(base, ret), dtype)