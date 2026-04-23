def nanquantile(x, q, axis=None, method="linear", keepdims=False):
    x = convert_to_tensor(x)
    q = convert_to_tensor(q)
    axis = to_tuple_or_list(axis)

    compute_dtype = dtypes.result_type(x.dtype, "float32")
    result_dtype = dtypes.result_type(x.dtype, float)

    x = cast(x, compute_dtype)
    if x.dtype != q.dtype:
        q = cast(q, x.dtype)

    if axis is None:
        y = reshape(x, [-1])
    else:
        axis = [canonicalize_axis(a, x.ndim) for a in axis]
        other_dims = sorted(set(range(x.ndim)).difference(axis))
        x_permed = torch.permute(x, dims=(other_dims + list(axis)))

        x_shape = list(x.shape)
        other_shape = [x_shape[i] for i in other_dims]
        end_shape = [math.prod([x_shape[i] for i in axis])]
        full_shape = other_shape + end_shape
        y = reshape(x_permed, full_shape)

    y = torch.nanquantile(y, q, dim=-1, interpolation=method)

    if keepdims:
        if axis is None:
            for _ in range(x.ndim):
                y = expand_dims(y, axis=-1)
        else:
            for i in sorted(axis):
                i = i + 1 if q.ndim > 0 else i
                y = expand_dims(y, axis=i)

    return cast(y, result_dtype)