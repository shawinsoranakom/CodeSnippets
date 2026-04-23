def test_glm_regression_unpenalized_vstacked_X(solver, fit_intercept, glm_dataset):
    """Test that unpenalized GLM converges for all solvers to correct solution.

    We work with a simple constructed data set with known solution.
    GLM fit on [X] is the same as fit on [X], [y]
                                         [X], [y].
    For wide X, [X', X'] is a singular matrix and we check against the minimum norm
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
        X = X[:, :-1]  # remove intercept
        intercept = coef[-1]
        coef = coef[:-1]
    else:
        intercept = 0
    X = np.concatenate((X, X), axis=0)
    assert np.linalg.matrix_rank(X) <= min(n_samples, n_features)
    y = np.r_[y, y]

    with warnings.catch_warnings():
        if solver.startswith("newton") and n_samples < n_features:
            # The newton solvers should warn and automatically fallback to LBFGS
            # in this case. The model should still converge.
            warnings.filterwarnings("ignore", category=scipy.linalg.LinAlgWarning)
        # XXX: Investigate if the ConvergenceWarning that can appear in some
        # cases should be considered a bug or not. In the mean time we don't
        # fail when the assertions below pass irrespective of the presence of
        # the warning.
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(X, y)

    if n_samples > n_features:
        rtol = 5e-5 if solver == "lbfgs" else 1e-6
        assert model.intercept_ == pytest.approx(intercept)
        assert_allclose(model.coef_, coef, rtol=rtol)
    else:
        # As it is an underdetermined problem, prediction = y. The following shows that
        # we get a solution, i.e. a (non-unique) minimum of the objective function ...
        rtol = 1e-6 if solver == "lbfgs" else 5e-6
        assert_allclose(model.predict(X), y, rtol=rtol)

        norm_solution = np.linalg.norm(np.r_[intercept, coef])
        norm_model = np.linalg.norm(np.r_[model.intercept_, model.coef_])
        if solver == "newton-cholesky":
            # XXX: This solver shows random behaviour. Sometimes it finds solutions
            # with norm_model <= norm_solution! So we check conditionally.
            if not (norm_model > (1 + 1e-12) * norm_solution):
                assert model.intercept_ == pytest.approx(intercept)
                assert_allclose(model.coef_, coef, rtol=1e-4)
        elif solver == "lbfgs" and fit_intercept:
            # Same as in test_glm_regression_unpenalized.
            # But it is not the minimum norm solution. Otherwise the norms would be
            # equal.
            assert norm_model > (1 + 1e-12) * norm_solution
        else:
            rtol = 1e-5 if solver == "newton-cholesky" else 1e-4
            assert model.intercept_ == pytest.approx(intercept, rel=rtol)
            assert_allclose(model.coef_, coef, rtol=rtol)