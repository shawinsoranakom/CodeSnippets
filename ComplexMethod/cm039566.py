def test_cdist(metric_param_grid, X, Y, csr_container):
    metric, param_grid = metric_param_grid
    keys = param_grid.keys()
    X_csr, Y_csr = csr_container(X), csr_container(Y)
    for vals in itertools.product(*param_grid.values()):
        kwargs = dict(zip(keys, vals))
        rtol_dict = {}
        if metric == "mahalanobis" and X.dtype == np.float32:
            # Computation of mahalanobis differs between
            # the scipy and scikit-learn implementation.
            # Hence, we increase the relative tolerance.
            # TODO: Inspect slight numerical discrepancy
            # with scipy
            rtol_dict = {"rtol": 1e-6}

        D_scipy_cdist = cdist(X, Y, metric, **kwargs)

        dm = DistanceMetric.get_metric(metric, X.dtype, **kwargs)

        # DistanceMetric.pairwise must be consistent for all
        # combinations of formats in {sparse, dense}.
        D_sklearn = dm.pairwise(X, Y)
        assert D_sklearn.flags.c_contiguous
        assert_allclose(D_sklearn, D_scipy_cdist, **rtol_dict)

        D_sklearn = dm.pairwise(X_csr, Y_csr)
        assert D_sklearn.flags.c_contiguous
        assert_allclose(D_sklearn, D_scipy_cdist, **rtol_dict)

        D_sklearn = dm.pairwise(X_csr, Y)
        assert D_sklearn.flags.c_contiguous
        assert_allclose(D_sklearn, D_scipy_cdist, **rtol_dict)

        D_sklearn = dm.pairwise(X, Y_csr)
        assert D_sklearn.flags.c_contiguous
        assert_allclose(D_sklearn, D_scipy_cdist, **rtol_dict)