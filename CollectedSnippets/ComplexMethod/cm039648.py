def test_ridge_regression_unpenalized(
    solver, fit_intercept, ols_ridge_dataset, global_random_seed
):
    """Test that unpenalized Ridge = OLS converges for all solvers to correct solution.

    We work with a simple constructed data set with known solution.
    Note: This checks the minimum norm solution for wide X, i.e.
    n_samples < n_features:
        min ||w||_2 subject to X w = y
    """
    X, y, coef, _ = ols_ridge_dataset
    n_samples, n_features = X.shape
    alpha = 0  # OLS
    params = dict(
        alpha=alpha,
        fit_intercept=fit_intercept,
        solver=solver,
        tol=1e-15 if solver in ("sag", "saga") else 1e-10,
        random_state=global_random_seed,
    )

    model = Ridge(**params)
    # Note that cholesky might give a warning: "Singular matrix in solving dual
    # problem. Using least-squares solution instead."
    if fit_intercept:
        X = X[:, :-1]  # remove intercept
        intercept = coef[-1]
        coef = coef[:-1]
    else:
        intercept = 0
    model.fit(X, y)

    # FIXME: `assert_allclose(model.coef_, coef)` should work for all cases but fails
    # for the wide/fat case with n_features > n_samples. The current Ridge solvers do
    # NOT return the minimum norm solution with fit_intercept=True.
    if n_samples > n_features or not fit_intercept:
        assert model.intercept_ == pytest.approx(intercept)
        assert_allclose(model.coef_, coef)
    else:
        # As it is an underdetermined problem, residuals = 0. This shows that we get
        # a solution to X w = y ....
        assert_allclose(model.predict(X), y)
        assert_allclose(X @ coef + intercept, y)
        # But it is not the minimum norm solution. (This should be equal.)
        assert np.linalg.norm(np.r_[model.intercept_, model.coef_]) > np.linalg.norm(
            np.r_[intercept, coef]
        )

        pytest.xfail(reason="Ridge does not provide the minimum norm solution.")
        assert model.intercept_ == pytest.approx(intercept)
        assert_allclose(model.coef_, coef)