def _has_known_nonnegative_scalar_int_value(arg: DTypeArg) -> bool:
    arg = _unwrap_dtype_arg(arg)

    if isinstance(arg, bool):
        return True
    if isinstance(arg, int):
        return arg >= 0

    dtype = getattr(arg, "dtype", None)
    if dtype is None or not is_integer_dtype(dtype):
        return False
    if dtype in _UNSIGNED_INT_DTYPES:
        return True

    lower = getattr(getattr(arg, "bounds", None), "lower", None)
    if lower is None:
        return False
    if isinstance(lower, sympy.Expr):
        return lower.is_nonnegative is True
    return lower >= 0