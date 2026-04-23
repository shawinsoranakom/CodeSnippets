def vdot(a: ArrayLike, b: ArrayLike, /):
    # 1. torch only accepts 1D arrays, numpy flattens
    # 2. torch requires matching dtype, while numpy casts (?)
    t_a, t_b = torch.atleast_1d(a, b)
    if t_a.ndim > 1:
        t_a = t_a.flatten()
    if t_b.ndim > 1:
        t_b = t_b.flatten()

    dtype = _dtypes_impl.result_type_impl(t_a, t_b)
    is_half = dtype == torch.float16 and (t_a.is_cpu or t_b.is_cpu)
    is_bool = dtype == torch.bool

    # work around torch's "dot" not implemented for 'Half', 'Bool'
    if is_half:
        dtype = torch.float32
    elif is_bool:
        dtype = torch.uint8

    t_a = _util.cast_if_needed(t_a, dtype)
    t_b = _util.cast_if_needed(t_b, dtype)

    result = torch.vdot(t_a, t_b)

    if is_half:
        result = result.to(torch.float16)
    elif is_bool:
        result = result.to(torch.bool)

    return result