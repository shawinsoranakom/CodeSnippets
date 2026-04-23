def test_logistic_regression_solvers_multiclass_unpenalized(
    fit_intercept, global_random_seed
):
    """Test and compare solver results for unpenalized multinomial multiclass."""
    # We want to avoid perfect separation.
    n_samples, n_features, n_classes = 100, 4, 3
    rng = np.random.RandomState(global_random_seed)
    X = make_low_rank_matrix(
        n_samples=n_samples,
        n_features=n_features + fit_intercept,
        effective_rank=n_features + fit_intercept,
        tail_strength=0.1,
        random_state=rng,
    )
    if fit_intercept:
        X[:, -1] = 1
    U, s, Vt = svd(X)
    assert np.all(s > 1e-3)  # to be sure that X is not singular
    assert np.max(s) / np.min(s) < 100  # condition number of X
    if fit_intercept:
        X = X[:, :-1]
    coef = rng.uniform(low=1, high=3, size=n_features * n_classes)
    coef = coef.reshape(n_classes, n_features)
    intercept = rng.uniform(low=-1, high=1, size=n_classes) * fit_intercept
    raw_prediction = X @ coef.T + intercept

    loss = HalfMultinomialLoss(n_classes=n_classes)
    proba = loss.link.inverse(raw_prediction)
    # Only newer numpy version (1.22) support more dimensions on pvals.
    y = np.zeros(n_samples)
    for i in range(n_samples):
        y[i] = np.argwhere(rng.multinomial(n=1, pvals=proba[i, :]))[0, 0]

    tol = 1e-9
    params = dict(fit_intercept=fit_intercept, random_state=global_random_seed)
    solver_max_iter = {"lbfgs": 200, "sag": 10_000, "saga": 10_000}
    solver_tol = {"sag": 1e-8, "saga": 1e-8}
    regressors = {
        solver: LogisticRegression(
            C=np.inf,
            solver=solver,
            tol=solver_tol.get(solver, tol),
            max_iter=solver_max_iter.get(solver, 100),
            **params,
        ).fit(X, y)
        for solver in set(SOLVERS) - set(["liblinear"])
    }
    for solver in regressors.keys():
        # See the docstring of test_multinomial_identifiability_on_iris for reference.
        assert_allclose(
            regressors[solver].coef_.sum(axis=0), 0, atol=1e-10, err_msg=solver
        )

    for solver_1, solver_2 in itertools.combinations(regressors, r=2):
        assert_allclose(
            regressors[solver_1].coef_,
            regressors[solver_2].coef_,
            rtol=5e-3 if (solver_1 == "saga" or solver_2 == "saga") else 2e-3,
            err_msg=f"{solver_1} vs {solver_2}",
        )
        if fit_intercept:
            assert_allclose(
                regressors[solver_1].intercept_,
                regressors[solver_2].intercept_,
                rtol=5e-3 if (solver_1 == "saga" or solver_2 == "saga") else 1e-3,
                err_msg=f"{solver_1} vs {solver_2}",
            )