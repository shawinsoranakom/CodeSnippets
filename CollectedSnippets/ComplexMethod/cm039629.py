def test_n_iter(solver, use_legacy_attributes):
    # Test that self.n_iter_ has the correct format.
    X, y = iris.data, iris.target
    if solver == "lbfgs":
        # lbfgs requires scaling to avoid convergence warnings
        X = scale(X)

    n_classes = np.unique(y).shape[0]
    assert n_classes == 3

    # Also generate a binary classification sub-problem.
    y_bin = y.copy()
    y_bin[y_bin == 2] = 0

    n_Cs = 4
    n_cv_fold = 2
    n_l1_ratios = 1

    # Binary classification case
    clf = LogisticRegression(tol=1e-2, C=1.0, solver=solver, random_state=42)
    clf.fit(X, y_bin)
    assert clf.n_iter_.shape == (1,)

    clf_cv = LogisticRegressionCV(
        tol=1e-2,
        solver=solver,
        Cs=n_Cs,
        l1_ratios=(0.0,),  # TODO(1.10): remove l1_ratios because it is default now.
        cv=n_cv_fold,
        random_state=42,
        use_legacy_attributes=use_legacy_attributes,
        scoring="neg_log_loss",  # TODO(1.11): remove because it is default now
    )
    clf_cv.fit(X, y_bin)
    if use_legacy_attributes:
        assert clf_cv.n_iter_.shape == (1, n_cv_fold, n_Cs, n_l1_ratios)
    else:
        assert clf_cv.n_iter_.shape == (n_cv_fold, n_l1_ratios, n_Cs)

    # multinomial case
    if solver in ("liblinear",):
        # This solver only supports one-vs-rest multiclass classification.
        return

    # When using the multinomial objective function, there is a single
    # optimization problem to solve for all classes at once:
    clf.fit(X, y)
    assert clf.n_iter_.shape == (1,)

    clf_cv.fit(X, y)
    if use_legacy_attributes:
        assert clf_cv.n_iter_.shape == (1, n_cv_fold, n_Cs, n_l1_ratios)
    else:
        assert clf_cv.n_iter_.shape == (n_cv_fold, n_l1_ratios, n_Cs)