def test_estimator():
    omp = OrthogonalMatchingPursuit(n_nonzero_coefs=n_nonzero_coefs)
    omp.fit(X, y[:, 0])
    assert omp.coef_.shape == (n_features,)
    assert omp.intercept_.shape == ()
    assert np.count_nonzero(omp.coef_) <= n_nonzero_coefs

    omp.fit(X, y)
    assert omp.coef_.shape == (n_targets, n_features)
    assert omp.intercept_.shape == (n_targets,)
    assert np.count_nonzero(omp.coef_) <= n_targets * n_nonzero_coefs

    coef_normalized = omp.coef_[0].copy()
    omp.set_params(fit_intercept=True)
    omp.fit(X, y[:, 0])
    assert_array_almost_equal(coef_normalized, omp.coef_)

    omp.set_params(fit_intercept=False)
    omp.fit(X, y[:, 0])
    assert np.count_nonzero(omp.coef_) <= n_nonzero_coefs
    assert omp.coef_.shape == (n_features,)
    assert omp.intercept_ == 0

    omp.fit(X, y)
    assert omp.coef_.shape == (n_targets, n_features)
    assert omp.intercept_ == 0
    assert np.count_nonzero(omp.coef_) <= n_targets * n_nonzero_coefs