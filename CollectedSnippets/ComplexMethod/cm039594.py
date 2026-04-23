def _alpha_grid(
    X,
    y,
    Xy=None,
    l1_ratio=1.0,
    fit_intercept=True,
    eps=1e-3,
    n_alphas=100,
    sample_weight=None,
    *,
    positive: bool = False,
):
    """Compute the grid of alpha values for elastic net parameter search

    Computes alpha_max which results in coef=0 and then uses a multiplicative grid of
    length `eps`.
    `X` is never copied.

    Parameters
    ----------
    X : {array-like, sparse matrix} of shape (n_samples, n_features)
        Training data. Pass directly as Fortran-contiguous data to avoid
        unnecessary memory duplication

    y : ndarray of shape (n_samples,) or (n_samples, n_outputs)
        Target values

    Xy : array-like of shape (n_features,) or (n_features, n_outputs),\
         default=None
        Xy = np.dot(X.T, y) that can be precomputed.

    l1_ratio : float, default=1.0
        The elastic net mixing parameter, with ``0 < l1_ratio <= 1``.
        For ``l1_ratio = 0``, there would be no L1 penalty which is not supported
        for the generation of alphas.

    eps : float, default=1e-3
        Length of the path. ``eps=1e-3`` means that
        ``alpha_min / alpha_max = 1e-3``

    n_alphas : int, default=100
        Number of alphas along the regularization path

    fit_intercept : bool, default=True
        Whether to fit an intercept or not

    sample_weight : ndarray of shape (n_samples,), default=None

    positive : bool, default=False
        If set to True, forces coefficients to be positive.

    Returns
    -------
    np.ndarray
        Grid of alpha values.
    """
    if l1_ratio == 0:
        raise ValueError(
            "Automatic alpha grid generation is not supported for"
            " l1_ratio=0. Please supply a grid by providing "
            "your estimator with the appropriate `alphas=` "
            "argument."
        )
    if Xy is not None:
        Xyw = Xy
    else:
        if fit_intercept:
            # TODO: For y.ndim >> 1, think about avoiding memory of y = y - y.mean()
            y = y - np.average(y, axis=0, weights=sample_weight)
            if sparse.issparse(X):
                X_mean, _ = mean_variance_axis(X, axis=0, weights=sample_weight)
            else:
                X_mean = np.average(X, axis=0, weights=sample_weight)

        if sample_weight is None:
            yw = y
        else:
            if y.ndim > 1:
                yw = y * sample_weight.reshape(-1, 1)
            else:
                yw = y * sample_weight

        if fit_intercept:
            # Avoid copy of X, i.e. avoid explicitly computing X - X_mean
            if y.ndim > 1:
                Xyw = X.T @ yw - X_mean[:, None] * np.sum(yw, axis=0)
            else:
                Xyw = X.T @ yw - X_mean * np.sum(yw, axis=0)
        else:
            Xyw = X.T @ yw

    if Xyw.ndim == 1:
        Xyw = Xyw[:, np.newaxis]
    if sample_weight is not None:
        n_samples = sample_weight.sum()
    else:
        n_samples = X.shape[0]

    if not positive:
        # Compute np.max(np.sqrt(np.sum(Xyw**2, axis=1))). We switch sqrt and max to
        # avoid many computations of sqrt.
        alpha_max = np.sqrt(np.max(np.sum(Xyw**2, axis=1))) / (n_samples * l1_ratio)
    else:
        # We may safely assume Xyw.shape[1] == 1, MultiTask estimators do not support
        # positive constraints.
        alpha_max = max(0, np.max(Xyw)) / (n_samples * l1_ratio)

    if alpha_max <= np.finfo(np.float64).resolution:
        return np.full(n_alphas, np.finfo(np.float64).resolution)

    return np.geomspace(alpha_max, alpha_max * eps, num=n_alphas)