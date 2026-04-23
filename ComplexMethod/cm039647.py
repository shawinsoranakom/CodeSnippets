def test_ridge_regression(solver, fit_intercept, ols_ridge_dataset, global_random_seed):
    """Test that Ridge converges for all solvers to correct solution.

    We work with a simple constructed data set with known solution.
    """
    X, y, _, coef = ols_ridge_dataset
    alpha = 1.0  # because ols_ridge_dataset uses this.
    params = dict(
        alpha=alpha,
        fit_intercept=True,
        solver=solver,
        tol=1e-15 if solver in ("sag", "saga") else 1e-10,
        random_state=global_random_seed,
    )

    # Calculate residuals and R2.
    res_null = y - np.mean(y)
    res_Ridge = y - X @ coef
    R2_Ridge = 1 - np.sum(res_Ridge**2) / np.sum(res_null**2)

    model = Ridge(**params)
    X = X[:, :-1]  # remove intercept
    if fit_intercept:
        intercept = coef[-1]
    else:
        X = X - X.mean(axis=0)
        y = y - y.mean()
        intercept = 0
    model.fit(X, y)
    coef = coef[:-1]

    assert model.intercept_ == pytest.approx(intercept)
    assert_allclose(model.coef_, coef)
    assert model.score(X, y) == pytest.approx(R2_Ridge)

    # Same with sample_weight.
    model = Ridge(**params).fit(X, y, sample_weight=np.ones(X.shape[0]))
    assert model.intercept_ == pytest.approx(intercept)
    assert_allclose(model.coef_, coef)
    assert model.score(X, y) == pytest.approx(R2_Ridge)

    assert model.solver_ == solver