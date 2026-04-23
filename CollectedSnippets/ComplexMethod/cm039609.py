def _pre_fit(
    X,
    y,
    Xy,
    precompute,
    fit_intercept,
    copy,
    check_gram=True,
    sample_weight=None,
):
    """Function used at beginning of fit in linear models with L1 or L0 penalty.

    This function applies _preprocess_data and additionally computes the gram matrix
    `precompute` as needed as well as `Xy`.

    It is assumed that X, y and sample_weight are already validated.

    Returns
    -------
    X
    y
    X_offset
    y_offset
    X_scale
    precompute
    Xy
    """
    n_samples, n_features = X.shape

    if sparse.issparse(X):
        # copy is not needed here as X is not modified inplace when X is sparse
        copy = False
        precompute = False
        # Rescale X and y only in dense case. Sparse cd solver directly deals with
        # sample_weight.
        rescale_with_sw = False
    else:
        # copy was done in fit if necessary
        rescale_with_sw = True

    X, y, X_offset, y_offset, X_scale, _ = _preprocess_data(
        X,
        y,
        fit_intercept=fit_intercept,
        copy=copy,
        sample_weight=sample_weight,
        check_input=False,
        rescale_with_sw=rescale_with_sw,
    )

    if hasattr(precompute, "__array__"):
        if fit_intercept and not np.allclose(X_offset, np.zeros(n_features)):
            warnings.warn(
                (
                    "Gram matrix was provided but X was centered to fit "
                    "intercept: recomputing Gram matrix."
                ),
                UserWarning,
            )
            # TODO: instead of warning and recomputing, we could just center
            # the user provided Gram matrix a-posteriori (after making a copy
            # when `copy=True`).
            # recompute Gram
            precompute = "auto"
            Xy = None
        elif check_gram:
            # If we're going to use the user's precomputed gram matrix, we
            # do a quick check to make sure its not totally bogus.
            _check_precomputed_gram_matrix(X, precompute, X_offset, X_scale)

    # precompute if n_samples > n_features
    if isinstance(precompute, str) and precompute == "auto":
        precompute = n_samples > n_features

    if precompute is True:
        # make sure that the 'precompute' array is contiguous.
        precompute = np.empty(shape=(n_features, n_features), dtype=X.dtype, order="C")
        np.dot(X.T, X, out=precompute)

    if not hasattr(precompute, "__array__"):
        Xy = None  # cannot use Xy if precompute is not Gram

    if hasattr(precompute, "__array__") and Xy is None:
        common_dtype = np.result_type(X.dtype, y.dtype)
        if y.ndim == 1:
            # Xy is 1d, make sure it is contiguous.
            Xy = np.empty(shape=n_features, dtype=common_dtype, order="C")
            np.dot(X.T, y, out=Xy)
        else:
            # Make sure that Xy is always F contiguous even if X or y are not
            # contiguous: the goal is to make it fast to extract the data for a
            # specific target.
            n_targets = y.shape[1]
            Xy = np.empty(shape=(n_features, n_targets), dtype=common_dtype, order="F")
            np.dot(y.T, X, out=Xy.T)

    return X, y, X_offset, y_offset, X_scale, precompute, Xy