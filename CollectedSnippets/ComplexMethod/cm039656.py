def test_ridge_sample_weight_consistency(
    fit_intercept, sparse_container, data, solver, global_random_seed
):
    """Test that the impact of sample_weight is consistent.

    Note that this test is stricter than the common test
    check_sample_weight_equivalence alone.
    """
    # filter out solver that do not support sparse input
    if sparse_container is not None:
        if solver == "svd" or (solver in ("cholesky", "saga") and fit_intercept):
            pytest.skip("unsupported configuration")

    # XXX: this test is quite sensitive to the seed used to generate the data:
    # ideally we would like the test to pass for any global_random_seed but this is not
    # the case at the moment.
    rng = np.random.RandomState(42)
    n_samples = 12
    if data == "tall":
        n_features = n_samples // 2
    else:
        n_features = n_samples * 2

    X = rng.rand(n_samples, n_features)
    y = rng.rand(n_samples)
    if sparse_container is not None:
        X = sparse_container(X)
    params = dict(
        fit_intercept=fit_intercept,
        alpha=1.0,
        solver=solver,
        positive=(solver == "lbfgs"),
        random_state=global_random_seed,  # for sag/saga
        tol=1e-12,
    )

    # 1) sample_weight=np.ones(..) should be equivalent to sample_weight=None,
    # a special case of check_sample_weight_equivalence(name, reg), but we also
    # test with sparse input.
    reg = Ridge(**params).fit(X, y, sample_weight=None)
    coef = reg.coef_.copy()
    if fit_intercept:
        intercept = reg.intercept_
    sample_weight = np.ones_like(y)
    reg.fit(X, y, sample_weight=sample_weight)
    assert_allclose(reg.coef_, coef, rtol=1e-6)
    if fit_intercept:
        assert_allclose(reg.intercept_, intercept)

    # 2) setting elements of sample_weight to 0 is equivalent to removing these samples,
    # another special case of check_sample_weight_equivalence(name, reg), but we
    # also test with sparse input
    sample_weight = rng.uniform(low=0.01, high=2, size=X.shape[0])
    sample_weight[-5:] = 0
    y[-5:] *= 1000  # to make excluding those samples important
    reg.fit(X, y, sample_weight=sample_weight)
    coef = reg.coef_.copy()
    if fit_intercept:
        intercept = reg.intercept_
    reg.fit(X[:-5, :], y[:-5], sample_weight=sample_weight[:-5])
    assert_allclose(reg.coef_, coef, rtol=1e-6)
    if fit_intercept:
        assert_allclose(reg.intercept_, intercept)

    # 3) scaling of sample_weight should have no effect
    # Note: For models with penalty, scaling the penalty term might work.
    reg2 = Ridge(**params).set_params(alpha=np.pi * params["alpha"])
    reg2.fit(X, y, sample_weight=np.pi * sample_weight)
    if solver in ("sag", "saga") and not fit_intercept:
        pytest.xfail(f"Solver {solver} does fail test for scaling of sample_weight.")
    assert_allclose(reg2.coef_, coef, rtol=1e-6)
    if fit_intercept:
        assert_allclose(reg2.intercept_, intercept)

    # 4) check that multiplying sample_weight by 2 is equivalent
    # to repeating corresponding samples twice
    if sparse_container is not None:
        X = X.toarray()
    X2 = np.concatenate([X, X[: n_samples // 2]], axis=0)
    y2 = np.concatenate([y, y[: n_samples // 2]])
    sample_weight_1 = sample_weight.copy()
    sample_weight_1[: n_samples // 2] *= 2
    sample_weight_2 = np.concatenate(
        [sample_weight, sample_weight[: n_samples // 2]], axis=0
    )
    if sparse_container is not None:
        X = sparse_container(X)
        X2 = sparse_container(X2)
    reg1 = Ridge(**params).fit(X, y, sample_weight=sample_weight_1)
    reg2 = Ridge(**params).fit(X2, y2, sample_weight=sample_weight_2)
    assert_allclose(reg1.coef_, reg2.coef_)
    if fit_intercept:
        assert_allclose(reg1.intercept_, reg2.intercept_)