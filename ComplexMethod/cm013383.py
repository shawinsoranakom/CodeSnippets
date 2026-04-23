def average(
    a: ArrayLike,
    axis=None,
    weights: ArrayLike = None,
    returned=False,
    *,
    keepdims=False,
):
    if weights is None:
        result = mean(a, axis=axis)
        wsum = torch.as_tensor(a.numel() / result.numel(), dtype=result.dtype)
    else:
        if not a.dtype.is_floating_point:
            a = a.double()

        # axis & weights
        if a.shape != weights.shape:
            if axis is None:
                raise TypeError(
                    "Axis must be specified when shapes of a and weights differ."
                )
            if weights.ndim != 1:
                raise TypeError(
                    "1D weights expected when shapes of a and weights differ."
                )
            if weights.shape[0] != a.shape[axis]:
                raise ValueError(
                    "Length of weights not compatible with specified axis."
                )

            # setup weight to broadcast along axis
            weights = torch.broadcast_to(weights, (a.ndim - 1) * (1,) + weights.shape)
            weights = weights.swapaxes(-1, axis)

        # do the work
        result_dtype = _dtypes_impl.result_type_impl(a, weights)
        numerator = sum(a * weights, axis, dtype=result_dtype)
        wsum = sum(weights, axis, dtype=result_dtype)
        result = numerator / wsum

    # We process keepdims manually because the decorator does not deal with variadic returns
    if keepdims:
        result = _util.apply_keepdims(result, axis, a.ndim)

    if returned:
        if wsum.shape != result.shape:
            wsum = torch.broadcast_to(wsum, result.shape).clone()
        return result, wsum
    else:
        return result