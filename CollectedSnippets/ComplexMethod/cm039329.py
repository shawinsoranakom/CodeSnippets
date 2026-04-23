def _estimate_mi(
    X,
    y,
    *,
    discrete_features="auto",
    discrete_target=False,
    n_neighbors=3,
    copy=True,
    random_state=None,
    n_jobs=None,
):
    """Estimate mutual information between the features and the target.

    Parameters
    ----------
    X : array-like or sparse matrix, shape (n_samples, n_features)
        Feature matrix.

    y : array-like of shape (n_samples,)
        Target vector.

    discrete_features : {'auto', bool, array-like}, default='auto'
        If bool, then determines whether to consider all features discrete
        or continuous. If array, then it should be either a boolean mask
        with shape (n_features,) or array with indices of discrete features.
        If 'auto', it is assigned to False for dense `X` and to True for
        sparse `X`.

    discrete_target : bool, default=False
        Whether to consider `y` as a discrete variable.

    n_neighbors : int, default=3
        Number of neighbors to use for MI estimation for continuous variables,
        see [1]_ and [2]_. Higher values reduce variance of the estimation, but
        could introduce a bias.

    copy : bool, default=True
        Whether to make a copy of the given data. If set to False, the initial
        data will be overwritten.

    random_state : int, RandomState instance or None, default=None
        Determines random number generation for adding small noise to
        continuous variables in order to remove repeated values.
        Pass an int for reproducible results across multiple function calls.
        See :term:`Glossary <random_state>`.

    n_jobs : int, default=None
        The number of jobs to use for computing the mutual information.
        The parallelization is done on the columns of `X`.
        ``None`` means 1 unless in a :obj:`joblib.parallel_backend` context.
        ``-1`` means using all processors. See :term:`Glossary <n_jobs>`
        for more details.

        .. versionadded:: 1.5


    Returns
    -------
    mi : ndarray, shape (n_features,)
        Estimated mutual information between each feature and the target in
        nat units. A negative value will be replaced by 0.

    References
    ----------
    .. [1] A. Kraskov, H. Stogbauer and P. Grassberger, "Estimating mutual
           information". Phys. Rev. E 69, 2004.
    .. [2] B. C. Ross "Mutual Information between Discrete and Continuous
           Data Sets". PLoS ONE 9(2), 2014.
    """
    X, y = check_X_y(X, y, accept_sparse="csc", y_numeric=not discrete_target)
    n_samples, n_features = X.shape

    if isinstance(discrete_features, (str, bool)):
        if isinstance(discrete_features, str):
            if discrete_features == "auto":
                discrete_features = issparse(X)
            else:
                raise ValueError("Invalid string value for discrete_features.")
        discrete_mask = np.empty(n_features, dtype=bool)
        discrete_mask.fill(discrete_features)
    else:
        discrete_features = check_array(discrete_features, ensure_2d=False)
        if discrete_features.dtype != "bool":
            discrete_mask = np.zeros(n_features, dtype=bool)
            discrete_mask[discrete_features] = True
        else:
            discrete_mask = discrete_features

    continuous_mask = ~discrete_mask
    if np.any(continuous_mask) and issparse(X):
        raise ValueError("Sparse matrix `X` can't have continuous features.")

    rng = check_random_state(random_state)
    if np.any(continuous_mask):
        X = X.astype(np.float64, copy=copy)
        X[:, continuous_mask] = scale(
            X[:, continuous_mask], with_mean=False, copy=False
        )

        # Add small noise to continuous features as advised in Kraskov et. al.
        means = np.maximum(1, np.mean(np.abs(X[:, continuous_mask]), axis=0))
        X[:, continuous_mask] += (
            1e-10
            * means
            * rng.standard_normal(size=(n_samples, np.sum(continuous_mask)))
        )

    if not discrete_target:
        y = scale(y, with_mean=False)
        y += (
            1e-10
            * np.maximum(1, np.mean(np.abs(y)))
            * rng.standard_normal(size=n_samples)
        )

    mi = Parallel(n_jobs=n_jobs)(
        delayed(_compute_mi)(x, y, discrete_feature, discrete_target, n_neighbors)
        for x, discrete_feature in zip(_iterate_columns(X), discrete_mask)
    )

    return np.array(mi)