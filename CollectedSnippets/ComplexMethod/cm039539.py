def is_usable_for(cls, X, Y, metric) -> bool:
        """Return True if the dispatcher can be used for the
        given parameters.

        Parameters
        ----------
        X : {ndarray, sparse matrix} of shape (n_samples_X, n_features)
            Input data.

        Y : {ndarray, sparse matrix} of shape (n_samples_Y, n_features)
            Input data.

        metric : str, default='euclidean'
            The distance metric to use.
            For a list of available metrics, see the documentation of
            :class:`~sklearn.metrics.DistanceMetric`.

        Returns
        -------
        True if the dispatcher can be used, else False.
        """

        # FIXME: the current Cython implementation is too slow for a large number of
        # features. We temporarily disable it to fallback on SciPy's implementation.
        # See: https://github.com/scikit-learn/scikit-learn/issues/28191
        if (
            issparse(X)
            and issparse(Y)
            and isinstance(metric, str)
            and "euclidean" in metric
        ):
            return False

        def is_numpy_c_ordered(X):
            return hasattr(X, "flags") and getattr(X.flags, "c_contiguous", False)

        def is_valid_sparse_matrix(X):
            return (
                issparse(X)
                and X.format == "csr"
                and
                # TODO: support CSR matrices without non-zeros elements
                X.nnz > 0
                and
                # TODO: support CSR matrices with int64 indices and indptr
                # See: https://github.com/scikit-learn/scikit-learn/issues/23653
                X.indices.dtype == X.indptr.dtype == np.int32
            )

        is_usable = (
            get_config().get("enable_cython_pairwise_dist", True)
            and (is_numpy_c_ordered(X) or is_valid_sparse_matrix(X))
            and (is_numpy_c_ordered(Y) or is_valid_sparse_matrix(Y))
            and X.dtype == Y.dtype
            and X.dtype in (np.float32, np.float64)
            and (metric in cls.valid_metrics() or isinstance(metric, DistanceMetric))
        )

        return is_usable