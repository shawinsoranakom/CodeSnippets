def median(x, axis=None, keepdims=False):
    x = convert_to_tensor(x)
    compute_dtype = dtypes.result_type(x.dtype, "float32")
    result_dtype = dtypes.result_type(x.dtype, float)
    x = cast(x, compute_dtype)

    if axis is None and keepdims is False:
        return cast(torch.median(x), result_dtype)
    elif isinstance(axis, int):
        return cast(
            torch.median(x, dim=axis, keepdim=keepdims)[0], result_dtype
        )

    # support multiple axes
    if axis is None:
        y = reshape(x, [-1])
    else:
        # transpose
        axis = [canonicalize_axis(a, x.ndim) for a in axis]
        other_dims = sorted(set(range(x.ndim)).difference(axis))
        perm = other_dims + list(axis)
        x_permed = torch.permute(x, dims=perm)
        # reshape
        x_shape = list(x.shape)
        other_shape = [x_shape[i] for i in other_dims]
        end_shape = [math.prod([x_shape[i] for i in axis])]
        full_shape = other_shape + end_shape
        y = reshape(x_permed, full_shape)

    y = torch.median(y, dim=-1)[0]

    if keepdims:
        if axis is None:
            for _ in range(x.ndim):
                y = expand_dims(y, axis=-1)
        else:
            for i in sorted(axis):
                y = expand_dims(y, axis=i)

    return cast(y, result_dtype)