def test_gaussian_mixture_attributes():
    # test bad parameters
    rng = np.random.RandomState(0)
    X = rng.rand(10, 2)

    # test good parameters
    n_components, tol, n_init, max_iter, reg_covar = 2, 1e-4, 3, 30, 1e-1
    covariance_type, init_params = "full", "random"
    gmm = GaussianMixture(
        n_components=n_components,
        tol=tol,
        n_init=n_init,
        max_iter=max_iter,
        reg_covar=reg_covar,
        covariance_type=covariance_type,
        init_params=init_params,
    ).fit(X)

    assert gmm.n_components == n_components
    assert gmm.covariance_type == covariance_type
    assert gmm.tol == tol
    assert gmm.reg_covar == reg_covar
    assert gmm.max_iter == max_iter
    assert gmm.n_init == n_init
    assert gmm.init_params == init_params