def test_logistic_cv_folds_with_classes_missing(enable_metadata_routing, n_classes):
    """Test that LogisticRegressionCV correctly computes scores even when classes are
    missing on CV folds.
    """
    with config_context(enable_metadata_routing=enable_metadata_routing):
        y = np.array(["a", "a", "b", "b", "c", "c"])[: 2 * n_classes]
        X = np.arange(2 * n_classes)[:, None]

        # Test CV folds have missing class labels.
        cv = KFold(n_splits=n_classes)
        # Check this assumption.
        for train, test in cv.split(X, y):
            assert len(np.unique(y[train])) == n_classes - 1
            assert len(np.unique(y[test])) == 1
            assert set(y[train]) & set(y[test]) == set()

        clf = LogisticRegressionCV(
            cv=cv,
            scoring="neg_brier_score",
            Cs=np.logspace(-6, 6, 5),
            l1_ratios=(0,),
            use_legacy_attributes=False,
        ).fit(X, y)

        assert clf.C_ == 1e-6  # smallest value of provided Cs
        for i, (train, test) in enumerate(cv.split(X, y)):
            # We need to construct the logistic regression model, clf2, as it was fit on
            # a single training fold.
            clf2 = LogisticRegression(C=clf.C_).fit(X, y)
            clf2.coef_ = clf.coefs_paths_[i, 0, 0, :, :-1]
            clf2.intercept_ = clf.coefs_paths_[i, 0, 0, :, -1]
            if n_classes <= 2:
                bs = brier_score_loss(
                    y[test],
                    clf2.predict_proba(X[test]),
                    pos_label="b",
                    labels=["a", "b"],
                )
            else:
                bs = brier_score_loss(
                    y[test], clf2.predict_proba(X[test]), labels=["a", "b", "c"]
                )

            assert_allclose(-clf.scores_[i, 0, 0], bs)