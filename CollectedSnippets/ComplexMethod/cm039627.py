def test_logistic_regression_solvers_multiclass(fit_intercept):
    """Test solvers converge to the same result for multiclass problems."""
    n_samples, n_features, n_classes = 20, 20, 3
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=10,
        n_classes=n_classes,
        random_state=0,
    )
    tol = 1e-8
    params = dict(fit_intercept=fit_intercept, tol=tol, random_state=42)

    # Override max iteration count for specific solvers to allow for
    # proper convergence.
    solver_max_iter = {"lbfgs": 200, "sag": 20_000, "saga": 20_000}

    classifiers = {
        solver: LogisticRegression(
            solver=solver, max_iter=solver_max_iter.get(solver, 100), **params
        ).fit(X, y)
        for solver in set(SOLVERS) - set(["liblinear"])
    }
    for solver, clf in classifiers.items():
        assert clf.coef_.shape == (n_classes, n_features), (
            f"Solver {solver} generates coef_ with wrong shape."
        )

    for solver_1, solver_2 in itertools.combinations(classifiers, r=2):
        assert_allclose(
            classifiers[solver_1].coef_,
            classifiers[solver_2].coef_,
            rtol=5e-3 if (solver_1 == "saga" or solver_2 == "saga") else 1e-3,
            err_msg=f"{solver_1} vs {solver_2}",
        )
        if fit_intercept:
            assert_allclose(
                classifiers[solver_1].intercept_,
                classifiers[solver_2].intercept_,
                rtol=5e-3 if (solver_1 == "saga" or solver_2 == "saga") else 1e-3,
                err_msg=f"{solver_1} vs {solver_2}",
            )

    # Test that LogisticRegressionCV gives almost the same results for the same C.
    # However, since in this case we take the average of the coefs after fitting across
    # all the folds, it need not be exactly the same.
    classifiers_cv = {
        solver: LogisticRegressionCV(
            Cs=[1.0],
            solver=solver,
            max_iter=solver_max_iter.get(solver, 100),
            use_legacy_attributes=False,
            scoring="neg_log_loss",  # TODO(1.11): remove because it is default now
            **params,
        ).fit(X, y)
        for solver in set(SOLVERS) - set(["liblinear"])
    }
    for solver in classifiers_cv:
        assert_allclose(
            classifiers_cv[solver].coef_, classifiers[solver].coef_, rtol=1e-2
        )
        if fit_intercept:
            assert_allclose(
                classifiers_cv[solver].intercept_,
                classifiers[solver].intercept_,
                rtol=1e-2,
            )