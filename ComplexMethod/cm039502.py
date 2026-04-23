def pairwise_kernels(
    X, Y=None, metric="linear", *, filter_params=False, n_jobs=None, **kwds
):
    """Compute the kernel between arrays X and optional array Y.

    This function takes one or two feature arrays or a kernel matrix, and returns
    a kernel matrix.

    - If `X` is a feature array, of shape (n_samples_X, n_features), and:

      - `Y` is `None` and `metric` is not 'precomputed', the pairwise kernels
        between `X` and itself are returned.
      - `Y` is a feature array of shape (n_samples_Y, n_features), the pairwise
        kernels between `X` and `Y` is returned.

    - If `X` is a kernel matrix, of shape (n_samples_X, n_samples_X), `metric`
      should be 'precomputed'. `Y` is thus ignored and `X` is returned as is.

    This method provides a safe way to take a kernel matrix as input, while
    preserving compatibility with many other algorithms that take a vector
    array.

    Valid values for metric are:
        ['additive_chi2', 'chi2', 'linear', 'poly', 'polynomial', 'rbf',
        'laplacian', 'sigmoid', 'cosine']

    Read more in the :ref:`User Guide <metrics>`.

    Parameters
    ----------
    X : {array-like, sparse matrix}  of shape (n_samples_X, n_samples_X) or \
            (n_samples_X, n_features)
        Array of pairwise kernels between samples, or a feature array.
        The shape of the array should be (n_samples_X, n_samples_X) if
        metric == "precomputed" and (n_samples_X, n_features) otherwise.

    Y : {array-like, sparse matrix} of shape (n_samples_Y, n_features), default=None
        A second feature array only if X has shape (n_samples_X, n_features).

    metric : str or callable, default="linear"
        The metric to use when calculating kernel between instances in a
        feature array. If metric is a string, it must be one of the metrics
        in ``pairwise.PAIRWISE_KERNEL_FUNCTIONS``.
        If metric is "precomputed", X is assumed to be a kernel matrix.
        Alternatively, if metric is a callable function, it is called on each
        pair of instances (rows) and the resulting value recorded. The callable
        should take two rows from X as input and return the corresponding
        kernel value as a single number. This means that callables from
        :mod:`sklearn.metrics.pairwise` are not allowed, as they operate on
        matrices, not single samples. Use the string identifying the kernel
        instead.

    filter_params : bool, default=False
        Whether to filter invalid parameters or not.

    n_jobs : int, default=None
        The number of jobs to use for the computation. This works by breaking
        down the pairwise matrix into n_jobs even slices and computing them
        using multithreading.

        ``None`` means 1 unless in a :obj:`joblib.parallel_backend` context.
        ``-1`` means using all processors. See :term:`Glossary <n_jobs>`
        for more details.

    **kwds : optional keyword parameters
        Any further parameters are passed directly to the kernel function.

    Returns
    -------
    K : ndarray of shape (n_samples_X, n_samples_X) or (n_samples_X, n_samples_Y)
        A kernel matrix K such that K_{i, j} is the kernel between the
        ith and jth vectors of the given matrix X, if Y is None.
        If Y is not None, then K_{i, j} is the kernel between the ith array
        from X and the jth array from Y.

    Notes
    -----
    If metric is a callable, no restrictions are placed on `X` and `Y` dimensions.

    Examples
    --------
    >>> from sklearn.metrics.pairwise import pairwise_kernels
    >>> X = [[0, 0, 0], [1, 1, 1]]
    >>> Y = [[1, 0, 0], [1, 1, 0]]
    >>> pairwise_kernels(X, Y, metric='linear')
    array([[0., 0.],
           [1., 2.]])
    """
    # import GPKernel locally to prevent circular imports
    from sklearn.gaussian_process.kernels import Kernel as GPKernel

    if metric == "precomputed":
        X, _ = check_pairwise_arrays(X, Y, precomputed=True)
        return X
    elif isinstance(metric, GPKernel):
        func = metric.__call__
    elif metric in PAIRWISE_KERNEL_FUNCTIONS:
        if filter_params:
            kwds = {k: kwds[k] for k in kwds if k in KERNEL_PARAMS[metric]}
        func = PAIRWISE_KERNEL_FUNCTIONS[metric]
    elif callable(metric):
        func = partial(_pairwise_callable, metric=metric, **kwds)

    return _parallel_pairwise(X, Y, func, n_jobs, **kwds)