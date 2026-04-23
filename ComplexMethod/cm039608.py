def _rescale_data(X, y, sample_weight, inplace=False):
    """Rescale data sample-wise by square root of sample_weight.

    For many linear models, this enables easy support for sample_weight because

        (y - X w)' S (y - X w)

    with S = diag(sample_weight) becomes

        ||y_rescaled - X_rescaled w||_2^2

    when setting

        y_rescaled = sqrt(S) y
        X_rescaled = sqrt(S) X

    The parameter `inplace` only takes effect for dense X and dense y.

    Returns
    -------
    X_rescaled : {array-like, sparse matrix}

    y_rescaled : {array-like, sparse matrix}

    sample_weight_sqrt : array-like of shape (n_samples,)
    """
    # Assume that _validate_data and _check_sample_weight have been called by
    # the caller.
    xp, _ = get_namespace(X, y, sample_weight)
    n_samples = X.shape[0]
    sample_weight_sqrt = xp.sqrt(sample_weight)

    if sp.issparse(X) or sp.issparse(y):
        sw_matrix = sparse.dia_array(
            (sample_weight_sqrt, 0), shape=(n_samples, n_samples)
        )

    if sp.issparse(X):
        X = safe_sparse_dot(sw_matrix, X)
    else:
        if inplace:
            X *= sample_weight_sqrt[:, None]
        else:
            X = X * sample_weight_sqrt[:, None]

    if sp.issparse(y):
        y = safe_sparse_dot(sw_matrix, y)
    else:
        if inplace:
            if y.ndim == 1:
                y *= sample_weight_sqrt
            else:
                y *= sample_weight_sqrt[:, None]
        else:
            if y.ndim == 1:
                y = y * sample_weight_sqrt
            else:
                y = y * sample_weight_sqrt[:, None]
    return _align_api_if_sparse(X), _align_api_if_sparse(y), sample_weight_sqrt