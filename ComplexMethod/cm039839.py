def _check_sample_weight(
    sample_weight,
    X,
    *,
    dtype=None,
    force_float_dtype=True,
    ensure_non_negative=False,
    ensure_same_device=True,
    copy=False,
    allow_all_zero_weights=False,
):
    """Validate sample weights.

    Note that passing sample_weight=None will output an array of ones.
    Therefore, in some cases, you may want to protect the call with:
    if sample_weight is not None:
        sample_weight = _check_sample_weight(...)

    Parameters
    ----------
    sample_weight : {ndarray, Number or None}, shape (n_samples,)
        Input sample weights.

    X : {ndarray, list, sparse matrix}
        Input data.

    dtype : dtype, default=None
        dtype of the validated `sample_weight`.
        If None, and `sample_weight` is an array:

            - If `sample_weight.dtype` is one of `{np.float64, np.float32}`,
              then the dtype is preserved.
            - Else the output has NumPy's default dtype: `np.float64`.

        If `dtype` is not `{np.float32, np.float64, None}`, then output will
        be `np.float64`.

    force_float_dtype : bool, default=True
        Whether `X` should be forced to be float dtype, when `dtype` is a non-float
        dtype or None.

    ensure_non_negative : bool, default=False,
        Whether or not the weights are expected to be non-negative.

        .. versionadded:: 1.0

    ensure_same_device : bool, default=True
        Whether `sample_weight` should be forced to be on the same device as `X`.

    copy : bool, default=False
        If True, a copy of sample_weight will be created.

    allow_all_zero_weights : bool, default=False,
        Whether or not to raise an error when sample weights are all zero.

    Returns
    -------
    sample_weight : ndarray of shape (n_samples,)
        Validated sample weight. It is guaranteed to be "C" contiguous.
    """
    xp, is_array_api, device = get_namespace_and_device(
        X, remove_types=(list, int, float)
    )

    n_samples = _num_samples(X)

    max_float_type = _max_precision_float_dtype(xp, device)
    float_dtypes = (
        [xp.float32] if max_float_type == xp.float32 else [xp.float64, xp.float32]
    )
    if force_float_dtype and dtype is not None and dtype not in float_dtypes:
        dtype = max_float_type

    if sample_weight is None:
        sample_weight = xp.ones(n_samples, dtype=dtype, device=device)
    elif isinstance(sample_weight, numbers.Number):
        sample_weight = xp.full(n_samples, sample_weight, dtype=dtype, device=device)
    else:
        if force_float_dtype and dtype is None:
            dtype = float_dtypes
        if is_array_api and ensure_same_device:
            sample_weight = xp.asarray(sample_weight, device=device)
        sample_weight = check_array(
            sample_weight,
            accept_sparse=False,
            ensure_2d=False,
            dtype=dtype,
            order="C",
            copy=copy,
            input_name="sample_weight",
        )
        if sample_weight.ndim != 1:
            raise ValueError(
                f"Sample weights must be 1D array or scalar, got "
                f"{sample_weight.ndim}D array. Expected either a scalar value "
                f"or a 1D array of length {n_samples}."
            )

        if sample_weight.shape != (n_samples,):
            raise ValueError(
                "sample_weight.shape == {}, expected {}!".format(
                    sample_weight.shape, (n_samples,)
                )
            )

    if not allow_all_zero_weights:
        if xp.all(sample_weight == 0):
            raise ValueError(
                "Sample weights must contain at least one non-zero number."
            )

    if ensure_non_negative:
        check_non_negative(sample_weight, "`sample_weight`")

    return sample_weight