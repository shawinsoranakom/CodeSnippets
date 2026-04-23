def cumprod(x, axis=None, dtype=None):
    if (
        is_integer_dtype(x.get_dtype()) or is_boolean_dtype(x.get_dtype())
    ) and dtype is None:
        dtype = torch.int64

    if len(x.get_size()) == 0:
        assert axis in [0, -1]
        dtype = dtype or x.get_dtype()
        return to_dtype(x, dtype, copy=True)

    def combine_fn(a_tuple, b_tuple):
        (a,) = a_tuple
        (b,) = b_tuple
        return (ops.mul(a, b),)

    kwargs = _make_scan_inner(x, axis=axis, dtype=dtype)
    (result,) = ir.Scan.create(**kwargs, combine_fn=combine_fn)
    if result is None:
        return fallback_cumprod(x, dim=axis, dtype=dtype)
    return result