def test_logistic_cv(global_random_seed, use_legacy_attributes):
    # test for LogisticRegressionCV object
    n_samples, n_features, n_cv = 50, 5, 3
    rng = np.random.RandomState(global_random_seed)
    X_ref = rng.randn(n_samples, n_features)
    y = np.sign(X_ref.dot(5 * rng.randn(n_features)))
    X_ref -= X_ref.mean()
    X_ref /= X_ref.std()
    lr_cv = LogisticRegressionCV(
        Cs=[1.0],
        l1_ratios=(0.0,),  # TODO(1.10): remove because it is default now.
        fit_intercept=False,
        random_state=global_random_seed,
        solver="liblinear",
        cv=n_cv,
        scoring="neg_log_loss",  # TODO(1.11): remove because it is default now
        use_legacy_attributes=use_legacy_attributes,
    )
    lr_cv.fit(X_ref, y)
    lr = LogisticRegression(
        C=1.0, fit_intercept=False, random_state=global_random_seed, solver="liblinear"
    )
    lr.fit(X_ref, y)
    assert_array_almost_equal(lr.coef_, lr_cv.coef_)

    assert lr_cv.coef_.shape == (1, n_features)
    assert_array_equal(lr_cv.classes_, [-1, 1])
    assert len(lr_cv.classes_) == 2
    assert lr_cv.Cs_.shape == (1,)
    n_Cs = lr_cv.Cs_.shape[0]
    assert lr_cv.l1_ratios_.shape == (1,)
    n_l1_ratios = lr_cv.l1_ratios_.shape[0]
    if use_legacy_attributes:
        coefs_paths = np.asarray(list(lr_cv.coefs_paths_.values()))
        assert coefs_paths.shape == (1, n_cv, n_Cs, n_l1_ratios, n_features)
        scores = np.asarray(list(lr_cv.scores_.values()))
        assert scores.shape == (1, n_cv, n_Cs, n_l1_ratios)
    else:
        assert lr_cv.coefs_paths_.shape == (n_cv, n_l1_ratios, n_Cs, 1, n_features)
        assert isinstance(lr_cv.C_, float)
        assert isinstance(lr_cv.l1_ratio_, float)
        assert lr_cv.scores_.shape == (n_cv, n_l1_ratios, n_Cs)