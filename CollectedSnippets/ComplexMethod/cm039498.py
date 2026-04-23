def pairwise_distances_argmin(X, Y, *, axis=1, metric="euclidean", metric_kwargs=None):
    """Compute minimum distances between one point and a set of points.

    This function computes for each row in X, the index of the row of Y which
    is closest (according to the specified distance).

    This is mostly equivalent to calling::

        pairwise_distances(X, Y=Y, metric=metric).argmin(axis=axis)

    but uses much less memory, and is faster for large arrays.

    This function works with dense 2D arrays only.

    Parameters
    ----------
    X : {array-like, sparse matrix} of shape (n_samples_X, n_features)
        Array containing points.

    Y : {array-like, sparse matrix} of shape (n_samples_Y, n_features)
        Arrays containing points.

    axis : int, default=1
        Axis along which the argmin and distances are to be computed.

    metric : str or callable, default="euclidean"
        Metric to use for distance computation. Any metric from scikit-learn
        or :mod:`scipy.spatial.distance` can be used.

        If metric is a callable function, it is called on each
        pair of instances (rows) and the resulting value recorded. The callable
        should take two arrays as input and return one value indicating the
        distance between them. This works for Scipy's metrics, but is less
        efficient than passing the metric name as a string.

        Distance matrices are not supported.

        Valid values for metric are:

        - from scikit-learn: ['cityblock', 'cosine', 'euclidean', 'l1', 'l2',
          'manhattan', 'nan_euclidean']

        - from :mod:`scipy.spatial.distance`: ['braycurtis', 'canberra', 'chebyshev',
          'correlation', 'dice', 'hamming', 'jaccard', 'kulsinski',
          'mahalanobis', 'minkowski', 'rogerstanimoto', 'russellrao',
          'seuclidean', 'sokalmichener', 'sokalsneath', 'sqeuclidean',
          'yule']

        See the documentation for :mod:`scipy.spatial.distance` for details on these
        metrics.

        .. note::
           `'kulsinski'` is deprecated from SciPy 1.9 and will be removed in SciPy 1.11.

        .. note::
           `'matching'` has been removed in SciPy 1.9 (use `'hamming'` instead).

    metric_kwargs : dict, default=None
        Keyword arguments to pass to specified metric function.

    Returns
    -------
    argmin : numpy.ndarray
        Y[argmin[i], :] is the row in Y that is closest to X[i, :].

    See Also
    --------
    pairwise_distances : Distances between every pair of samples of X and Y.
    pairwise_distances_argmin_min : Same as `pairwise_distances_argmin` but also
        returns the distances.

    Examples
    --------
    >>> from sklearn.metrics.pairwise import pairwise_distances_argmin
    >>> X = [[0, 0, 0], [1, 1, 1]]
    >>> Y = [[1, 0, 0], [1, 1, 0]]
    >>> pairwise_distances_argmin(X, Y)
    array([0, 1])
    """
    ensure_all_finite = "allow-nan" if metric == "nan_euclidean" else True
    X, Y = check_pairwise_arrays(X, Y, ensure_all_finite=ensure_all_finite)
    xp, _ = get_namespace(X, Y)

    if axis == 0:
        X, Y = Y, X

    if metric_kwargs is None:
        metric_kwargs = {}

    if ArgKmin.is_usable_for(X, Y, metric) and _is_numpy_namespace(xp):
        # This is an adaptor for one "sqeuclidean" specification.
        # For this backend, we can directly use "sqeuclidean".
        if metric_kwargs.get("squared", False) and metric == "euclidean":
            metric = "sqeuclidean"
            metric_kwargs = {}

        indices = ArgKmin.compute(
            X=X,
            Y=Y,
            k=1,
            metric=metric,
            metric_kwargs=metric_kwargs,
            strategy="auto",
            return_distance=False,
        )
        indices = indices.flatten()
    else:
        # Joblib-based backend, which is used when user-defined callable
        # are passed for metric.

        # This won't be used in the future once PairwiseDistancesReductions support:
        #   - DistanceMetrics which work on supposedly binary data
        #   - CSR-dense and dense-CSR case if 'euclidean' in metric.

        # Turn off check for finiteness because this is costly and because arrays
        # have already been validated.
        with config_context(assume_finite=True):
            indices = xp.concat(
                list(
                    pairwise_distances_chunked(
                        X, Y, reduce_func=_argmin_reduce, metric=metric, **metric_kwargs
                    )
                ),
                axis=0,
            )

    return indices