def pairwise_distances(
    X,
    Y=None,
    metric="euclidean",
    *,
    n_jobs=None,
    ensure_all_finite=True,
    **kwds,
):
    """Compute the distance matrix from a feature array X and optional Y.

    This function takes one or two feature arrays or a distance matrix, and returns
    a distance matrix.

    - If `X` is a feature array, of shape (n_samples_X, n_features), and:

      - `Y` is `None` and `metric` is not 'precomputed', the pairwise distances
        between `X` and itself are returned.
      - `Y` is a feature array of shape (n_samples_Y, n_features), the pairwise
        distances between `X` and `Y` is returned.

    - If `X` is a distance matrix, of shape (n_samples_X, n_samples_X), `metric`
      should be 'precomputed'. `Y` is thus ignored and `X` is returned as is.

    If the input is a collection of non-numeric data (e.g. a list of strings or a
    boolean array), a custom metric must be passed.

    This method provides a safe way to take a distance matrix as input, while
    preserving compatibility with many other algorithms that take a vector
    array.

    Valid values for metric are:

    - From scikit-learn: ['cityblock', 'cosine', 'euclidean', 'l1', 'l2',
      'manhattan', 'nan_euclidean']. All metrics support sparse matrix
      inputs except 'nan_euclidean'.

    - From :mod:`scipy.spatial.distance`: ['braycurtis', 'canberra', 'chebyshev',
      'correlation', 'dice', 'hamming', 'jaccard', 'kulsinski', 'mahalanobis',
      'minkowski', 'rogerstanimoto', 'russellrao', 'seuclidean',
      'sokalmichener', 'sokalsneath', 'sqeuclidean', 'yule'].
      These metrics do not support sparse matrix inputs.

    .. note::
        `'kulsinski'` is deprecated from SciPy 1.9 and will be removed in SciPy 1.11.

    .. note::
        `'matching'` has been removed in SciPy 1.9 (use `'hamming'` instead).

    Note that in the case of 'cityblock', 'cosine' and 'euclidean' (which are
    valid :mod:`scipy.spatial.distance` metrics), the scikit-learn implementation
    will be used, which is faster and has support for sparse matrices (except
    for 'cityblock'). For a verbose description of the metrics from
    scikit-learn, see :func:`sklearn.metrics.pairwise.distance_metrics`
    function.

    Read more in the :ref:`User Guide <metrics>`.

    Parameters
    ----------
    X : {array-like, sparse matrix} of shape (n_samples_X, n_samples_X) or \
            (n_samples_X, n_features)
        Array of pairwise distances between samples, or a feature array.
        The shape of the array should be (n_samples_X, n_samples_X) if
        metric == "precomputed" and (n_samples_X, n_features) otherwise.

    Y : {array-like, sparse matrix} of shape (n_samples_Y, n_features), default=None
        An optional second feature array. Only allowed if
        metric != "precomputed".

    metric : str or callable, default='euclidean'
        The metric to use when calculating distance between instances in a
        feature array. If metric is a string, it must be one of the options
        allowed by :func:`scipy.spatial.distance.pdist` for its metric parameter, or
        a metric listed in ``pairwise.PAIRWISE_DISTANCE_FUNCTIONS``.
        If metric is "precomputed", X is assumed to be a distance matrix.
        Alternatively, if metric is a callable function, it is called on each
        pair of instances (rows) and the resulting value recorded. The callable
        should take two arrays from X as input and return a value indicating
        the distance between them.

    n_jobs : int, default=None
        The number of jobs to use for the computation. This works by breaking
        down the pairwise matrix into n_jobs even slices and computing them
        using multithreading.

        ``None`` means 1 unless in a :obj:`joblib.parallel_backend` context.
        ``-1`` means using all processors. See :term:`Glossary <n_jobs>`
        for more details.

        The "euclidean" and "cosine" metrics rely heavily on BLAS which is already
        multithreaded. So, increasing `n_jobs` would likely cause oversubscription
        and quickly degrade performance.

    ensure_all_finite : bool or 'allow-nan', default=True
        Whether to raise an error on np.inf, np.nan, pd.NA in array. Ignored
        for a metric listed in ``pairwise.PAIRWISE_DISTANCE_FUNCTIONS``. The
        possibilities are:

        - True: Force all values of array to be finite.
        - False: accepts np.inf, np.nan, pd.NA in array.
        - 'allow-nan': accepts only np.nan and pd.NA values in array. Values
          cannot be infinite.

        .. versionadded:: 1.6
           `force_all_finite` was renamed to `ensure_all_finite`.

    **kwds : optional keyword parameters
        Any further parameters are passed directly to the distance function.
        If using a scipy.spatial.distance metric, the parameters are still
        metric dependent. See the scipy docs for usage examples.

    Returns
    -------
    D : ndarray of shape (n_samples_X, n_samples_X) or \
            (n_samples_X, n_samples_Y)
        A distance matrix D such that D_{i, j} is the distance between the
        ith and jth vectors of the given matrix X, if Y is None.
        If Y is not None, then D_{i, j} is the distance between the ith array
        from X and the jth array from Y.

    See Also
    --------
    pairwise_distances_chunked : Performs the same calculation as this
        function, but returns a generator of chunks of the distance matrix, in
        order to limit memory usage.
    sklearn.metrics.pairwise.paired_distances : Computes the distances between
        corresponding elements of two arrays.

    Notes
    -----
    If metric is a callable, no restrictions are placed on `X` and `Y` dimensions.

    Examples
    --------
    >>> from sklearn.metrics.pairwise import pairwise_distances
    >>> X = [[0, 0, 0], [1, 1, 1]]
    >>> Y = [[1, 0, 0], [1, 1, 0]]
    >>> pairwise_distances(X, Y, metric='sqeuclidean')
    array([[1., 2.],
           [2., 1.]])
    """

    if metric == "precomputed":
        X, _ = check_pairwise_arrays(
            X, Y, precomputed=True, ensure_all_finite=ensure_all_finite
        )

        whom = (
            "`pairwise_distances`. Precomputed distance "
            " need to have non-negative values."
        )
        check_non_negative(X, whom=whom)
        return X
    elif metric in PAIRWISE_DISTANCE_FUNCTIONS:
        func = PAIRWISE_DISTANCE_FUNCTIONS[metric]
    elif callable(metric):
        func = partial(
            _pairwise_callable,
            metric=metric,
            ensure_all_finite=ensure_all_finite,
            **kwds,
        )
    else:
        if issparse(X) or issparse(Y):
            raise TypeError("scipy distance metrics do not support sparse matrices.")

        dtype = bool if metric in PAIRWISE_BOOLEAN_FUNCTIONS else "infer_float"

        if dtype is bool and (X.dtype != bool or (Y is not None and Y.dtype != bool)):
            msg = "Data was converted to boolean for metric %s" % metric
            warnings.warn(msg, DataConversionWarning)

        X, Y = check_pairwise_arrays(
            X, Y, dtype=dtype, ensure_all_finite=ensure_all_finite
        )

        # precompute data-derived metric params
        params = _precompute_metric_params(X, Y, metric=metric, **kwds)
        kwds.update(**params)

        if effective_n_jobs(n_jobs) == 1 and X is Y:
            return distance.squareform(distance.pdist(X, metric=metric, **kwds))
        func = partial(distance.cdist, metric=metric, **kwds)

    return _parallel_pairwise(X, Y, func, n_jobs, **kwds)