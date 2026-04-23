def test_gaussian_mixture_precisions_init_diag(global_dtype):
    """Check that we properly initialize `precision_cholesky_` when we manually
    provide the precision matrix.

    In this regard, we check the consistency between estimating the precision
    matrix and providing the same precision matrix as initialization. It should
    lead to the same results with the same number of iterations.

    If the initialization is wrong then the number of iterations will increase.

    Non-regression test for:
    https://github.com/scikit-learn/scikit-learn/issues/16944
    """
    # generate a toy dataset
    n_samples = 300
    rng = np.random.RandomState(0)
    shifted_gaussian = rng.randn(n_samples, 2) + np.array([20, 20])
    C = np.array([[0.0, -0.7], [3.5, 0.7]])
    stretched_gaussian = np.dot(rng.randn(n_samples, 2), C)
    X = np.vstack([shifted_gaussian, stretched_gaussian]).astype(global_dtype)

    # common parameters to check the consistency of precision initialization
    n_components, covariance_type, reg_covar, random_state = 2, "diag", 1e-6, 0

    # execute the manual initialization to compute the precision matrix:
    # - run KMeans to have an initial guess
    # - estimate the covariance
    # - compute the precision matrix from the estimated covariance
    resp = np.zeros((X.shape[0], n_components)).astype(global_dtype)
    label = (
        KMeans(n_clusters=n_components, n_init=1, random_state=random_state)
        .fit(X)
        .labels_
    )
    resp[np.arange(X.shape[0]), label] = 1
    _, _, covariance = _estimate_gaussian_parameters(
        X, resp, reg_covar=reg_covar, covariance_type=covariance_type
    )
    assert covariance.dtype == global_dtype
    precisions_init = 1 / covariance

    gm_with_init = GaussianMixture(
        n_components=n_components,
        covariance_type=covariance_type,
        reg_covar=reg_covar,
        precisions_init=precisions_init,
        random_state=random_state,
    ).fit(X)
    assert gm_with_init.means_.dtype == global_dtype
    assert gm_with_init.covariances_.dtype == global_dtype
    assert gm_with_init.precisions_cholesky_.dtype == global_dtype

    gm_without_init = GaussianMixture(
        n_components=n_components,
        covariance_type=covariance_type,
        reg_covar=reg_covar,
        random_state=random_state,
    ).fit(X)
    assert gm_without_init.means_.dtype == global_dtype
    assert gm_without_init.covariances_.dtype == global_dtype
    assert gm_without_init.precisions_cholesky_.dtype == global_dtype

    assert gm_without_init.n_iter_ == gm_with_init.n_iter_
    assert_allclose(
        gm_with_init.precisions_cholesky_, gm_without_init.precisions_cholesky_
    )