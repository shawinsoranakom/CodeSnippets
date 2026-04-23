def linspace(
    start: NumberType | TensorLikeType,
    end: NumberType | TensorLikeType,
    steps: NumberType,
    *,
    dtype: torch.dtype | None = None,
    device: DeviceLikeType | None = None,
    layout: torch.layout = torch.strided,
    pin_memory: bool = False,
    requires_grad: bool = False,
) -> TensorLikeType:
    if isinstance(start, TensorLikeType):
        torch._check(
            start.dim() == 0,
            lambda: "linspace only supports 0-dimensional start and end tensors",
        )
        start = _maybe_convert_to_dtype(start, highest_precision_float(device))
    if isinstance(end, TensorLikeType):
        torch._check(
            end.dim() == 0,
            lambda: "linspace only supports 0-dimensional start and end tensors",
        )
        end = _maybe_convert_to_dtype(end, highest_precision_float(device))

    if builtins.any(isinstance(arg, complex) for arg in (start, end, steps)):
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
        raise AssertionError(f"steps must be IntLike, got {type(steps)}")  # for mypy
    torch._check(steps >= 0, lambda: "number of steps must be non-negative")

    factory_kwargs = {
        "layout": layout,
        "device": device,
        "pin_memory": pin_memory,
        "requires_grad": requires_grad,
    }
    if steps == 0:
        return torch.full((0,), 0, dtype=dtype, **factory_kwargs)  # type: ignore[arg-type]
    if steps == 1:
        if isinstance(start, TensorLikeType):
            empty_tensor = torch.empty((steps,), dtype=dtype, **factory_kwargs)  # type: ignore[arg-type]
            return torch.ops.aten.copy.default(empty_tensor, start)
        else:
            return torch.full((steps,), start, dtype=dtype, **factory_kwargs)  # type: ignore[arg-type]

    # Perform in arange in int because some backends like ATen or Triton do not support all the dtypes
    rg = torch.arange(0, steps, **factory_kwargs)  # type: ignore[arg-type]

    # Small types need to be computed in higher precision as this is, at heart, an associative scan
    dtype_red = (
        torch.int64
        if (utils.is_boolean_dtype(dtype) or utils.is_integer_dtype(dtype))
        else dtype
    )
    computation_dtype, _ = utils.reduction_dtypes(
        rg, REDUCTION_OUTPUT_TYPE_KIND.SAME, dtype_red
    )
    cast_rg = partial(_maybe_convert_to_dtype, dtype=computation_dtype)

    # We implement torch.lerp without performing rg / (steps - 1) explicitly
    # With this we get out[0] == start, out[-1] == end
    step = (end - start) / (steps - 1)
    # pyrefly: ignore [no-matching-overload]
    out = torch.where(
        rg < steps / 2,
        start + step * cast_rg(rg),  # type: ignore[arg-type,operator]
        end - step * cast_rg((steps - 1) - rg),  # type: ignore[arg-type,operator]
    )
    return _maybe_convert_to_dtype(out, dtype)