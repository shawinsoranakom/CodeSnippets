def test_glm_regression_unpenalized_hstacked_X(solver, fit_intercept, glm_dataset):
    """Test that unpenalized GLM converges for all solvers to correct solution.

    We work with a simple constructed data set with known solution.
    GLM fit on [X] is the same as fit on [X, X]/2.
    For long X, [X, X] is a singular matrix and we check against the minimum norm
    solution:
        min ||w||_2 subject to w = argmin deviance(X, y, w)
    """
    model, X, y, coef, _, _, _ = glm_dataset
    n_samples, n_features = X.shape
    alpha = 0  # unpenalized
    params = dict(
        alpha=alpha,
        fit_intercept=fit_intercept,
        solver=solver,
        tol=1e-12,
        max_iter=1000,
    )

    model = clone(model).set_params(**params)
    if fit_intercept:
        intercept = coef[-1]
        coef = coef[:-1]
        if n_samples > n_features:
            X = X[:, :-1]  # remove intercept
            X = 0.5 * np.concatenate((X, X), axis=1)
        else:
            # To know the minimum norm solution, we keep one intercept column and do
            # not divide by 2. Later on, we must take special care.
            X = np.c_[X[:, :-1], X[:, :-1], X[:, -1]]
    else:
        intercept = 0
        X = 0.5 * np.concatenate((X, X), axis=1)
    assert np.linalg.matrix_rank(X) <= min(n_samples, n_features)

    with warnings.catch_warnings():
        if solver.startswith("newton"):
            # The newton solvers should warn and automatically fallback to LBFGS
            # in this case. The model should still converge.
            warnings.filterwarnings("ignore", category=scipy.linalg.LinAlgWarning)
        # XXX: Investigate if the ConvergenceWarning that can appear in some
        # cases should be considered a bug or not. In the mean time we don't
        # fail when the assertions below pass irrespective of the presence of
        # the warning.
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(X, y)

    if fit_intercept and n_samples < n_features:
        # Here we take special care.
        model_intercept = 2 * model.intercept_
        model_coef = 2 * model.coef_[:-1]  # exclude the other intercept term.
        # For minimum norm solution, we would have
        # assert model.intercept_ == pytest.approx(model.coef_[-1])
    else:
        model_intercept = model.intercept_
        model_coef = model.coef_

    if n_samples > n_features:
        assert model_intercept == pytest.approx(intercept)
        rtol = 1e-4
        assert_allclose(model_coef, np.r_[coef, coef], rtol=rtol)
    else:
        # As it is an underdetermined problem, prediction = y. The following shows that
        # we get a solution, i.e. a (non-unique) minimum of the objective function ...
        rtol = 1e-6 if solver == "lbfgs" else 5e-6
        assert_allclose(model.predict(X), y, rtol=rtol)
        if (solver == "lbfgs" and fit_intercept) or solver == "newton-cholesky":
            # Same as in test_glm_regression_unpenalized.
            # But it is not the minimum norm solution. Otherwise the norms would be
            # equal.
            norm_solution = np.linalg.norm(
                0.5 * np.r_[intercept, intercept, coef, coef]
            )
            norm_model = np.linalg.norm(np.r_[model.intercept_, model.coef_])
            assert norm_model > (1 + 1e-12) * norm_solution
            # For minimum norm solution, we would have
            # assert model.intercept_ == pytest.approx(model.coef_[-1])
        else:
            assert model_intercept == pytest.approx(intercept, rel=5e-6)
            assert_allclose(model_coef, np.r_[coef, coef], rtol=1e-4)