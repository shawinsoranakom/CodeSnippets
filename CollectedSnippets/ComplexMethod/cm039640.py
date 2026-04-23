def test_enet_sample_weight_consistency(
    estimator, fit_intercept, alpha, precompute, sparse_container, global_random_seed
):
    """Test that the impact of sample_weight is consistent.

    Note that this test is stricter than the common test
    check_sample_weight_equivalence alone and also tests sparse X.
    """
    rng = np.random.RandomState(global_random_seed)
    n_samples, n_features = 10, 5
    X = rng.rand(n_samples, n_features)
    y = rng.rand(n_samples)

    params = dict(
        alpha=alpha,
        fit_intercept=fit_intercept,
        tol=1e-6,
        l1_ratio=0.5,
    )

    if issubclass(estimator, MultiTaskElasticNet):
        n_tasks = 3
        y = np.tile(y[:, None], reps=(1, n_tasks))
        if precompute:
            return
    else:
        n_tasks = 1
        params["precompute"] = precompute

    if sparse_container is not None:
        X = sparse_container(X)

    reg = estimator(**params).fit(X, y)
    coef = reg.coef_.copy()
    if fit_intercept:
        intercept = reg.intercept_
    assert np.sum(coef != 0) > 1

    # 1) sample_weight=np.ones(..) should be equivalent to sample_weight=None
    sample_weight = np.ones_like(y, shape=y.shape[0])
    reg.fit(X, y, sample_weight=sample_weight)
    assert_allclose(reg.coef_, coef, rtol=1e-6)
    if fit_intercept:
        assert_allclose(reg.intercept_, intercept)

    # 2) sample_weight=None should be equivalent to sample_weight = number
    sample_weight = 123.0
    reg.fit(X, y, sample_weight=sample_weight)
    assert_allclose(reg.coef_, coef, rtol=1e-6)
    if fit_intercept:
        assert_allclose(reg.intercept_, intercept)

    # 3) scaling of sample_weight should have no effect, cf. np.average()
    sample_weight = rng.uniform(low=0.01, high=2, size=X.shape[0])
    reg = reg.fit(X, y, sample_weight=sample_weight)
    coef = reg.coef_.copy()
    if fit_intercept:
        intercept = reg.intercept_

    reg.fit(X, y, sample_weight=np.pi * sample_weight)
    assert_allclose(reg.coef_, coef, rtol=1e-6)
    if fit_intercept:
        assert_allclose(reg.intercept_, intercept)

    # 4) setting elements of sample_weight to 0 is equivalent to removing these samples
    sample_weight_0 = sample_weight.copy()
    sample_weight_0[-5:] = 0
    y[-5:] *= 1000  # to make excluding those samples important
    reg.fit(X, y, sample_weight=sample_weight_0)
    coef_0 = reg.coef_.copy()
    if fit_intercept:
        intercept_0 = reg.intercept_
    reg.fit(X[:-5], y[:-5], sample_weight=sample_weight[:-5])
    assert_allclose(reg.coef_, coef_0, rtol=1e-6)
    if fit_intercept:
        assert_allclose(reg.intercept_, intercept_0)

    # 5) check that multiplying sample_weight by 2 is equivalent to repeating
    # corresponding samples twice
    if sparse_container is not None:
        X2 = sparse.vstack([X, X[: n_samples // 2]], format="csc")
    else:
        X2 = np.concatenate([X, X[: n_samples // 2]], axis=0)
    y2 = np.concatenate([y, y[: n_samples // 2]], axis=0)
    sample_weight_1 = sample_weight.copy()
    sample_weight_1[: n_samples // 2] *= 2
    sample_weight_2 = np.concatenate(
        [sample_weight, sample_weight[: n_samples // 2]], axis=0
    )

    reg1 = estimator(**params).fit(X, y, sample_weight=sample_weight_1)
    reg2 = estimator(**params).fit(X2, y2, sample_weight=sample_weight_2)
    assert_allclose(reg1.coef_, reg2.coef_, rtol=1e-6)