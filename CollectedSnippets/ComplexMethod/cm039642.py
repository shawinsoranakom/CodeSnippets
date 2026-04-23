def test_enet_cv_sample_weight_consistency(
    estimator, l1_ratio, fit_intercept, precompute, sparse_container
):
    """Test that the impact of sample_weight is consistent."""
    rng = np.random.RandomState(0)
    n_samples, n_features = 10, 5

    X = rng.rand(n_samples, n_features)
    y = X.sum(axis=1) + rng.rand(n_samples)
    params = dict(
        fit_intercept=fit_intercept,
        precompute=precompute,
        tol=1e-6,
        cv=3,
    )
    if l1_ratio > 0:
        params["l1_ratio"] = l1_ratio
    if issubclass(estimator, (MultiTaskElasticNetCV, MultiTaskLassoCV)):
        n_tasks = 3
        y = np.tile(y[:, None], reps=(1, n_tasks))
        params.pop("precompute")
    if sparse_container is not None:
        X = sparse_container(X)

    reg = estimator(**params).fit(X, y)
    coef = reg.coef_.copy()
    if fit_intercept:
        intercept = reg.intercept_
    assert np.sum(coef != 0) > 1

    # sample_weight=np.ones(..) should be equivalent to sample_weight=None
    sample_weight = np.ones(n_samples)
    reg.fit(X, y, sample_weight=sample_weight)
    assert_allclose(reg.coef_, coef, rtol=1e-6)
    if fit_intercept:
        assert_allclose(reg.intercept_, intercept)

    # sample_weight=None should be equivalent to sample_weight = number
    sample_weight = 123.0
    reg.fit(X, y, sample_weight=sample_weight)
    assert_allclose(reg.coef_, coef, rtol=1e-6)
    if fit_intercept:
        assert_allclose(reg.intercept_, intercept)

    # scaling of sample_weight should have no effect, cf. np.average()
    sample_weight = 2 * np.ones(n_samples)
    reg.fit(X, y, sample_weight=sample_weight)
    assert_allclose(reg.coef_, coef, rtol=1e-6)
    if fit_intercept:
        assert_allclose(reg.intercept_, intercept)