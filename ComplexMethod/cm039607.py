def _preprocess_data(
    X,
    y,
    *,
    fit_intercept,
    copy=True,
    sample_weight=None,
    check_input=True,
    rescale_with_sw=True,
):
    """Common data preprocessing for fitting linear models.

    This helper is in charge of the following steps:

    - `sample_weight` is assumed to be `None` or a validated array with same dtype as
      `X`.
    - If `check_input=True`, perform standard input validation of `X`, `y`.
    - Perform copies if requested to avoid side-effects in case of inplace
      modifications of the input.

    Then, if `fit_intercept=True` this preprocessing centers both `X` and `y` as
    follows:
        - if `X` is dense, center the data and
        store the mean vector in `X_offset`.
        - if `X` is sparse, store the mean in `X_offset`
        without centering `X`. The centering is expected to be handled by the
        linear solver where appropriate.
        - in either case, always center `y` and store the mean in `y_offset`.
        - both `X_offset` and `y_offset` are always weighted by `sample_weight`
          if not set to `None`.

    If `fit_intercept=False`, no centering is performed and `X_offset`, `y_offset`
    are set to zero.

    If `rescale_with_sw` is True, then X and y are rescaled with the square root of
    sample weights.

    Returns
    -------
    X_out : {ndarray, sparse matrix} of shape (n_samples, n_features)
        If copy=True a copy of the input X is triggered, otherwise operations are
        inplace.
        If input X is dense, then X_out is centered.
    y_out : {ndarray, sparse matrix} of shape (n_samples,) or (n_samples, n_targets)
        Centered copy of y.
    X_offset : ndarray of shape (n_features,)
        The mean per column of input X.
    y_offset : float or ndarray of shape (n_features,)
    X_scale : ndarray of shape (n_features,)
        Always an array of ones. TODO: refactor the code base to make it
        possible to remove this unused variable.
    sample_weight_sqrt : ndarray of shape (n_samples, ) or None
        `np.sqrt(sample_weight)`
    """
    xp, _, device_ = get_namespace_and_device(X, y, sample_weight)
    n_samples, n_features = X.shape
    X_is_sparse = sp.issparse(X)

    if check_input:
        X = check_array(
            X, copy=copy, accept_sparse=["csr", "csc"], dtype=supported_float_dtypes(xp)
        )
        y = check_array(y, dtype=X.dtype, copy=True, ensure_2d=False)
    else:
        y = xp.astype(y, X.dtype)
        if copy:
            if X_is_sparse:
                X = X.copy()
            else:
                X = _asarray_with_order(X, order="K", copy=True, xp=xp)

    dtype_ = X.dtype

    if fit_intercept:
        if X_is_sparse:
            X_offset, X_var = mean_variance_axis(X, axis=0, weights=sample_weight)
        else:
            X_offset = _average(X, axis=0, weights=sample_weight, xp=xp)

            X_offset = xp.astype(X_offset, X.dtype, copy=False)
            X -= X_offset

        y_offset = _average(y, axis=0, weights=sample_weight, xp=xp)
        y -= y_offset
    else:
        X_offset = xp.zeros(n_features, dtype=X.dtype, device=device_)
        if y.ndim == 1:
            y_offset = xp.asarray(0.0, dtype=dtype_, device=device_)
        else:
            y_offset = xp.zeros(y.shape[1], dtype=dtype_, device=device_)

    # X_scale is no longer needed. It is a historic artifact from the
    # time where linear model exposed the normalize parameter.
    X_scale = xp.ones(n_features, dtype=X.dtype, device=device_)

    if sample_weight is not None and rescale_with_sw:
        # Sample weight can be implemented via a simple rescaling.
        # For sparse X and y, it triggers copies anyway.
        # For dense X and y that already have been copied, we safely do inplace
        # rescaling.
        # Hence, inplace=True here regardless of copy.
        X, y, sample_weight_sqrt = _rescale_data(X, y, sample_weight, inplace=True)
    else:
        sample_weight_sqrt = None
    return X, y, X_offset, y_offset, X_scale, sample_weight_sqrt