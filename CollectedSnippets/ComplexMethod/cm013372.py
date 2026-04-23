def arange(
    start: ArrayLikeOrScalar | None = None,
    stop: ArrayLikeOrScalar | None = None,
    step: ArrayLikeOrScalar | None = 1,
    dtype: DTypeLike | None = None,
    *,
    like: NotImplementedType = None,
):
    if step == 0:
        raise ZeroDivisionError
    if stop is None and start is None:
        raise TypeError
    if stop is None:
        # XXX: this breaks if start is passed as a kwarg:
        # arange(start=4) should raise (no stop) but doesn't
        start, stop = 0, start
    if start is None:
        start = 0

    # the dtype of the result
    if dtype is None:
        dtype = (
            _dtypes_impl.default_dtypes().float_dtype
            if any(_dtypes_impl.is_float_or_fp_tensor(x) for x in (start, stop, step))
            else _dtypes_impl.default_dtypes().int_dtype
        )
    work_dtype = torch.float64 if dtype.is_complex else dtype

    # RuntimeError: "lt_cpu" not implemented for 'ComplexFloat'. Fall back to eager.
    if any(_dtypes_impl.is_complex_or_complex_tensor(x) for x in (start, stop, step)):
        raise NotImplementedError

    if (step > 0 and start > stop) or (step < 0 and start < stop):
        # empty range
        return torch.empty(0, dtype=dtype)

    result = torch.arange(start, stop, step, dtype=work_dtype)
    result = _util.cast_if_needed(result, dtype)
    return result