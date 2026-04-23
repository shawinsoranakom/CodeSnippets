def test_multinomial_cv_iris(use_legacy_attributes):
    # Test that multinomial LogisticRegressionCV is correct using the iris dataset.
    X, y = iris.data, iris.target
    n_samples, n_features = X.shape

    # The cv indices from stratified kfold
    n_cv = 2
    cv = StratifiedKFold(n_cv)
    precomputed_folds = list(cv.split(X, y))

    # Train clf on the original dataset
    clf = LogisticRegressionCV(
        cv=precomputed_folds,
        solver="newton-cholesky",
        use_legacy_attributes=True,
        scoring="neg_log_loss",  # TODO(1.11): remove because it is default now
    )
    clf.fit(X, y)

    # Test the shape of various attributes.
    assert clf.coef_.shape == (3, n_features)
    assert_array_equal(clf.classes_, [0, 1, 2])
    coefs_paths = np.asarray(list(clf.coefs_paths_.values()))
    assert coefs_paths.shape == (3, n_cv, 10, n_features + 1)
    assert clf.Cs_.shape == (10,)
    scores = np.asarray(list(clf.scores_.values()))
    assert scores.shape == (3, n_cv, 10)

    # Test that for the iris data multinomial gives a better accuracy than OvR
    clf_ovr = GridSearchCV(
        OneVsRestClassifier(LogisticRegression(solver="newton-cholesky")),
        {"estimator__C": np.logspace(-4, 4, num=10)},
        scoring="neg_log_loss",
    ).fit(X, y)
    for solver in ["lbfgs", "newton-cg", "sag", "saga"]:
        max_iter = 500 if solver in ["sag", "saga"] else 30
        clf_multi = LogisticRegressionCV(
            solver=solver,
            max_iter=max_iter,
            random_state=42,
            tol=1e-3 if solver in ["sag", "saga"] else 1e-2,
            cv=2,
            scoring="neg_log_loss",  # TODO(1.11): remove because it is default now
            use_legacy_attributes=use_legacy_attributes,
        )
        if solver == "lbfgs":
            # lbfgs requires scaling to avoid convergence warnings
            X = scale(X)

        clf_multi.fit(X, y)
        multi_score = clf_multi.score(X, y)
        ovr_score = clf_ovr.score(X, y)
        assert multi_score > ovr_score

        # Test attributes of LogisticRegressionCV
        assert clf.coef_.shape == clf_multi.coef_.shape
        assert_array_equal(clf_multi.classes_, [0, 1, 2])
        if use_legacy_attributes:
            coefs_paths = np.asarray(list(clf_multi.coefs_paths_.values()))
            assert coefs_paths.shape == (3, n_cv, 10, n_features + 1)
            assert clf_multi.Cs_.shape == (10,)
            scores = np.asarray(list(clf_multi.scores_.values()))
            assert scores.shape == (3, n_cv, 10)

            # Norm of coefficients should increase with increasing C.
            for fold in range(clf_multi.coefs_paths_[0].shape[0]):
                # with use_legacy_attributes=True, coefs_paths_ is a dict whose keys
                # are classes and each value has shape
                # (n_folds, n_l1_ratios, n_cs, n_features)
                # Note that we have to exclude the intercept, hence the ':-1'
                # on the last dimension
                coefs = [
                    clf_multi.coefs_paths_[c][fold, :, :-1] for c in clf_multi.classes_
                ]
                coefs = np.swapaxes(coefs, 1, 0).reshape(len(clf_multi.Cs_), -1)
                norms = np.sum(coefs * coefs, axis=1)  # L2 norm for each C
                assert np.all(np.diff(norms) >= 0)
        else:
            n_folds, n_cs, n_l1_ratios, n_classes, n_dof = 2, 10, 1, 3, n_features + 1
            assert clf_multi.coefs_paths_.shape == (
                n_folds,
                n_l1_ratios,
                n_cs,
                n_classes,
                n_dof,
            )
            assert isinstance(clf_multi.C_, float)
            assert isinstance(clf_multi.l1_ratio_, float)
            assert clf_multi.scores_.shape == (n_folds, n_l1_ratios, n_cs)

            # Norm of coefficients should increase with increasing C.
            for fold in range(clf_multi.coefs_paths_.shape[0]):
                # with use_legacy_attributes=False, coefs_paths_ has shape
                # (n_folds, n_l1_ratios, n_Cs, n_classes, n_features + 1)
                # Note that we have to exclude the intercept, hence the ':-1'
                # on the last dimension
                coefs = clf_multi.coefs_paths_[fold, 0, :, :, :-1]
                norms = np.sum(coefs * coefs, axis=(-2, -1))  # L2 norm for each C
                assert np.all(np.diff(norms) >= 0)

    # Test CV folds with missing class labels:
    # The iris target variable has 3 classes and is ordered such that a simple
    # CV split with 3 folds separates the classes.
    cv = KFold(n_splits=3)
    # Check this assumption.
    classes = np.unique(y)
    assert len(classes) == 3
    for train, test in cv.split(X, y):
        assert len(np.unique(y[train])) == 2
        assert len(np.unique(y[test])) == 1
        assert set(y[train]) & set(y[test]) == set()

    clf = LogisticRegressionCV(
        cv=cv,
        use_legacy_attributes=False,
        scoring="accuracy",
    ).fit(X, y)
    # We expect accuracy to be exactly 0 because train and test sets have
    # non-overlapping labels
    assert np.all(clf.scores_ == 0.0)

    # We use a proper scoring rule, i.e. the Brier score, to evaluate our classifier.
    # We set small Cs, that is strong penalty as the best C is likely the smallest one.
    clf = LogisticRegressionCV(
        cv=cv,
        scoring="neg_brier_score",
        Cs=np.logspace(-6, 3, 10),
        use_legacy_attributes=False,
    ).fit(X, y)
    assert clf.C_ == 1e-6  # smallest value of provided Cs
    brier_scores = -clf.scores_
    # We expect the scores to be bad because train and test sets have
    # non-overlapping labels
    assert np.all(brier_scores > 0.7 * 2)  # times 2 because scale_by_half=False
    # But the best score should be better than the worst value of 1.
    assert np.min(brier_scores) < 0.8 * 2