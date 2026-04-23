def test_linear_regression_sample_weight_consistency(
    X_shape, sparse_container, fit_intercept, global_random_seed
):
    """Test that the impact of sample_weight is consistent.

    Note that this test is stricter than the common test
    check_sample_weight_equivalence alone and also tests sparse X.
    It is very similar to test_enet_sample_weight_consistency.
    """
    rng = np.random.RandomState(global_random_seed)
    n_samples, n_features = X_shape

    X = rng.rand(n_samples, n_features)
    y = rng.rand(n_samples)
    if sparse_container is not None:
        X = sparse_container(X)
    params = dict(fit_intercept=fit_intercept)

    reg = LinearRegression(**params).fit(X, y, sample_weight=None)
    coef = reg.coef_.copy()
    if fit_intercept:
        intercept = reg.intercept_

    # 1) sample_weight=np.ones(..) must be equivalent to sample_weight=None,
    # a special case of check_sample_weight_equivalence(name, reg), but we also
    # test with sparse input.
    sample_weight = np.ones_like(y)
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
    assert_allclose(reg.coef_, coef, rtol=1e-6 if sparse_container is None else 1e-5)
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
    assert_allclose(reg.coef_, coef_0, rtol=1e-5)
    if fit_intercept:
        assert_allclose(reg.intercept_, intercept_0)

    # 5) check that multiplying sample_weight by 2 is equivalent to repeating
    # corresponding samples twice
    if sparse_container is not None:
        X2 = sparse.vstack([X, X[: n_samples // 2]], format="csc")
    else:
        X2 = np.concatenate([X, X[: n_samples // 2]], axis=0)
    y2 = np.concatenate([y, y[: n_samples // 2]])
    sample_weight_1 = sample_weight.copy()
    sample_weight_1[: n_samples // 2] *= 2
    sample_weight_2 = np.concatenate(
        [sample_weight, sample_weight[: n_samples // 2]], axis=0
    )

    reg1 = LinearRegression(**params).fit(X, y, sample_weight=sample_weight_1)
    reg2 = LinearRegression(**params).fit(X2, y2, sample_weight=sample_weight_2)
    assert_allclose(reg1.coef_, reg2.coef_, rtol=1e-6)
    if fit_intercept:
        assert_allclose(reg1.intercept_, reg2.intercept_)