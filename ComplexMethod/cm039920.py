def _average(a, axis=None, weights=None, normalize=True, xp=None):
    """Partial port of np.average to support the Array API.

    It does a best effort at mimicking the return dtype rule described at
    https://numpy.org/doc/stable/reference/generated/numpy.average.html but
    only for the common cases needed in scikit-learn.
    """
    xp, _, device_ = get_namespace_and_device(a, weights, xp=xp)

    if _is_numpy_namespace(xp):
        if normalize:
            return xp.asarray(numpy.average(a, axis=axis, weights=weights))
        elif axis is None and weights is not None:
            return xp.asarray(numpy.dot(a, weights))

    a = xp.asarray(a, device=device_)
    if weights is not None:
        weights = xp.asarray(weights, device=device_)

    if weights is not None and a.shape != weights.shape:
        if axis is None:
            raise TypeError(
                f"Axis must be specified when the shape of a {tuple(a.shape)} and "
                f"weights {tuple(weights.shape)} differ."
            )

        if tuple(weights.shape) != (a.shape[axis],):
            raise ValueError(
                f"Shape of weights weights.shape={tuple(weights.shape)} must be "
                f"consistent with a.shape={tuple(a.shape)} and {axis=}."
            )

        # If weights are 1D, add singleton dimensions for broadcasting
        shape = [1] * a.ndim
        shape[axis] = a.shape[axis]
        weights = xp.reshape(weights, tuple(shape))

    if xp.isdtype(a.dtype, "complex floating"):
        raise NotImplementedError(
            "Complex floating point values are not supported by average."
        )
    if weights is not None and xp.isdtype(weights.dtype, "complex floating"):
        raise NotImplementedError(
            "Complex floating point values are not supported by average."
        )

    output_dtype = _find_matching_floating_dtype(a, weights, xp=xp)
    a = xp.astype(a, output_dtype)

    if weights is None:
        return (xp.mean if normalize else xp.sum)(a, axis=axis)

    weights = xp.astype(weights, output_dtype)

    sum_ = xp.sum(xp.multiply(a, weights), axis=axis)

    if not normalize:
        return sum_

    scale = xp.sum(weights, axis=axis)
    if xp.any(scale == 0.0):
        raise ZeroDivisionError("Weights sum to zero, can't be normalized")

    return sum_ / scale