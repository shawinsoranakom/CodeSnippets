def test_ridge_cv_individual_penalties():
    # Tests the ridge_cv object optimizing individual penalties for each target

    rng = np.random.RandomState(42)

    # Create random dataset with multiple targets. Each target should have
    # a different optimal alpha.
    n_samples, n_features, n_targets = 20, 5, 3
    y = rng.randn(n_samples, n_targets)
    X = (
        np.dot(y[:, [0]], np.ones((1, n_features)))
        + np.dot(y[:, [1]], 0.05 * np.ones((1, n_features)))
        + np.dot(y[:, [2]], 0.001 * np.ones((1, n_features)))
        + rng.randn(n_samples, n_features)
    )

    alphas = (1, 100, 1000)

    # Find optimal alpha for each target
    optimal_alphas = [RidgeCV(alphas=alphas).fit(X, target).alpha_ for target in y.T]

    # Find optimal alphas for all targets simultaneously
    ridge_cv = RidgeCV(alphas=alphas, alpha_per_target=True).fit(X, y)
    assert_array_equal(optimal_alphas, ridge_cv.alpha_)

    # The resulting regression weights should incorporate the different
    # alpha values.
    assert_array_almost_equal(
        Ridge(alpha=ridge_cv.alpha_).fit(X, y).coef_, ridge_cv.coef_
    )

    # Test shape of alpha_ and cv_results_
    ridge_cv = RidgeCV(alphas=alphas, alpha_per_target=True, store_cv_results=True).fit(
        X, y
    )
    assert ridge_cv.alpha_.shape == (n_targets,)
    assert ridge_cv.best_score_.shape == (n_targets,)
    assert ridge_cv.cv_results_.shape == (n_samples, len(alphas), n_targets)

    # Test edge case of there being only one alpha value
    ridge_cv = RidgeCV(alphas=1, alpha_per_target=True, store_cv_results=True).fit(X, y)
    assert ridge_cv.alpha_.shape == (n_targets,)
    assert ridge_cv.best_score_.shape == (n_targets,)
    assert ridge_cv.cv_results_.shape == (n_samples, n_targets, 1)

    # Test edge case of there being only one target
    ridge_cv = RidgeCV(alphas=alphas, alpha_per_target=True, store_cv_results=True).fit(
        X, y[:, 0]
    )
    assert np.isscalar(ridge_cv.alpha_)
    assert np.isscalar(ridge_cv.best_score_)
    assert ridge_cv.cv_results_.shape == (n_samples, len(alphas))

    # Try with a custom scoring function
    ridge_cv = RidgeCV(alphas=alphas, alpha_per_target=True, scoring="r2").fit(X, y)
    assert_array_equal(optimal_alphas, ridge_cv.alpha_)
    assert_array_almost_equal(
        Ridge(alpha=ridge_cv.alpha_).fit(X, y).coef_, ridge_cv.coef_
    )

    # Using a custom CV object should throw an error in combination with
    # alpha_per_target=True
    ridge_cv = RidgeCV(alphas=alphas, cv=LeaveOneOut(), alpha_per_target=True)
    msg = "cv!=None and alpha_per_target=True are incompatible"
    with pytest.raises(ValueError, match=msg):
        ridge_cv.fit(X, y)
    ridge_cv = RidgeCV(alphas=alphas, cv=6, alpha_per_target=True)
    with pytest.raises(ValueError, match=msg):
        ridge_cv.fit(X, y)