def test_cross_validate_return_indices(global_random_seed):
    """Check the behaviour of `return_indices` in `cross_validate`."""
    X, y = load_iris(return_X_y=True)
    X = scale(X)  # scale features for better convergence
    estimator = LogisticRegression()

    cv = KFold(n_splits=3, shuffle=True, random_state=global_random_seed)
    cv_results = cross_validate(estimator, X, y, cv=cv, n_jobs=2, return_indices=False)
    assert "indices" not in cv_results

    cv_results = cross_validate(estimator, X, y, cv=cv, n_jobs=2, return_indices=True)
    assert "indices" in cv_results
    train_indices = cv_results["indices"]["train"]
    test_indices = cv_results["indices"]["test"]
    assert len(train_indices) == cv.n_splits
    assert len(test_indices) == cv.n_splits

    assert_array_equal([indices.size for indices in train_indices], 100)
    assert_array_equal([indices.size for indices in test_indices], 50)

    for split_idx, (expected_train_idx, expected_test_idx) in enumerate(cv.split(X, y)):
        assert_array_equal(train_indices[split_idx], expected_train_idx)
        assert_array_equal(test_indices[split_idx], expected_test_idx)