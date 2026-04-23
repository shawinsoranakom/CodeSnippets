def arange(
    start: NumberType = 0,
    end: NumberType | None = None,
    step: NumberType = 1,
    *,
    dtype: torch.dtype | None = None,
    layout: torch.layout = torch.strided,
    device: DeviceLikeType | None = None,
    pin_memory: bool = False,
    requires_grad: bool = False,
) -> TensorLikeType:
    utils.check_layout(layout)
    utils.check_pin_memory(pin_memory)
    device = torch.device(utils.device_or_default(device))

    if isinstance(start, complex):
        raise AssertionError("arange does not support complex start")
    if isinstance(end, complex):
        raise AssertionError("arange does not support complex end")
    if isinstance(step, complex):
        raise AssertionError("arange does not support complex step")

    # Case: torch.arange(5)
    if end is None:
        end = start
        start = 0
    torch._check(step != 0, lambda: "step must be nonzero")
    if step > 0:
        torch._check(
            end >= start,
            lambda: "upper bound and lower bound inconsistent with step sign",
        )
    elif step < 0:
        torch._check(
            end <= start,
            lambda: "upper bound and lower bound inconsistent with step sign",
        )

    def is_finite(x):
        return not isinstance(x, FloatWithoutSymFloat) or math.isfinite(x)

    torch._check(
        is_finite(start) and is_finite(end),
        lambda: f"unsupported range: {start} -> {end}",
    )
    torch._check(
        is_finite(step),
        lambda: f"step must be finite but got {step}",
    )

    args = (start, end, step)
    integer_args = builtins.all(isinstance(arg, IntLike) for arg in args)

    if dtype is None:
        dtype = torch.int64 if integer_args else torch.get_default_dtype()

    is_integer = utils.is_integer_dtype(dtype)
    if is_integer or integer_args:
        xstart = sym_int(start)
        xend = sym_int(end)
        xstep = sym_int(step)

    # For int64 we truncate arguments to int before calculating length, but
    # other integral dtypes we don't. Weird... but needed to match ATen shapes.
    if dtype == torch.int64 or integer_args:
        # Uses floordiv to avoid ceil in inductor.
        sgn = bool(xstep > 0) - bool(xstep < 0)  # type: ignore[possibly-undefined]
        length = (xend - xstart + xstep - sgn) // xstep  # type: ignore[possibly-undefined]
    else:
        length = math.ceil((end - start) / step)

    if is_integer:
        return prims.iota(
            length,
            start=xstart,  # type: ignore[possibly-undefined]
            step=xstep,  # type: ignore[possibly-undefined]
            dtype=dtype,
            device=device,
            requires_grad=requires_grad,
        )

    index = prims.iota(
        length,
        start=0,
        step=1,
        dtype=torch.int64,
        device=device,
        requires_grad=False,
    )

    computation_dtype = (
        torch.long if integer_args else utils.get_acc_type(dtype, device)
    )
    index = _maybe_convert_to_dtype(index, computation_dtype)
    result = start + step * index
    result = _maybe_convert_to_dtype(result, dtype)

    if requires_grad:
        result.requires_grad_(True)
    return result