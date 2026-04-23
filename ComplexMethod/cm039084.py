def _inverse_binarize_thresholding(y, output_type, classes, threshold, xp=None):
    """Inverse label binarization transformation using thresholding."""

    if output_type == "binary" and y.ndim == 2 and y.shape[1] > 2:
        raise ValueError("output_type='binary', but y.shape = {0}".format(y.shape))

    xp, _, device_ = get_namespace_and_device(y, xp=xp)
    classes = xp.asarray(classes, device=device_)

    if output_type != "binary" and y.shape[1] != classes.shape[0]:
        raise ValueError(
            "The number of class is not equal to the number of dimension of y."
        )

    dtype_ = _find_matching_floating_dtype(y, xp=xp)
    if hasattr(y, "dtype") and xp.isdtype(y.dtype, "integral"):
        int_dtype_ = y.dtype
    else:
        int_dtype_ = indexing_dtype(xp)

    # Perform thresholding
    if sp.issparse(y):
        if threshold > 0:
            if y.format not in ("csr", "csc"):
                y = y.tocsr()
            y.data = np.array(y.data > threshold, dtype=int)
            y.eliminate_zeros()
        else:
            y = xp.asarray(y.toarray() > threshold, dtype=int_dtype_, device=device_)
    else:
        y = xp.asarray(
            xp.asarray(y, dtype=dtype_, device=device_) > threshold,
            dtype=int_dtype_,
            device=device_,
        )

    # Inverse transform data
    if output_type == "binary":
        if sp.issparse(y):
            y = y.toarray()
        if y.ndim == 2 and y.shape[1] == 2:
            return classes[y[:, 1]]
        else:
            if classes.shape[0] == 1:
                return xp.repeat(classes[0], len(y))
            else:
                return classes[xp.reshape(y, (-1,))]

    elif output_type == "multilabel-indicator":
        return y

    else:
        raise ValueError("{0} format is not supported".format(output_type))