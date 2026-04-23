def test_encoding(categories, unknown_value, global_random_seed, smooth, target_type):
    """Check encoding for binary and continuous targets.

    Compare the values returned by `TargetEncoder.fit_transform` against the
    expected encodings for cv splits from a naive reference Python
    implementation in _encode_target.
    """

    n_categories = 3
    X_train_int_array = np.array([[0] * 20 + [1] * 30 + [2] * 40], dtype=np.int64).T
    X_test_int_array = np.array([[0, 1, 2]], dtype=np.int64).T
    n_samples = X_train_int_array.shape[0]

    if categories == "auto":
        X_train = X_train_int_array
        X_test = X_test_int_array
    else:
        X_train = categories[0][X_train_int_array]
        X_test = categories[0][X_test_int_array]

    X_test = np.concatenate((X_test, [[unknown_value]]))

    data_rng = np.random.RandomState(global_random_seed)
    n_splits = 3
    if target_type == "binary":
        y_numeric = data_rng.randint(low=0, high=2, size=n_samples)
        target_names = np.array(["cat", "dog"], dtype=object)
        y_train = target_names[y_numeric]

    else:
        assert target_type == "continuous"
        y_numeric = data_rng.uniform(low=-10, high=20, size=n_samples)
        y_train = y_numeric

    shuffled_idx = data_rng.permutation(n_samples)
    X_train_int_array = X_train_int_array[shuffled_idx]
    X_train = X_train[shuffled_idx]
    y_train = y_train[shuffled_idx]
    y_numeric = y_numeric[shuffled_idx]

    # Define our CV splitting strategy
    if target_type == "binary":
        cv = StratifiedKFold(
            n_splits=n_splits, random_state=global_random_seed, shuffle=True
        )
    else:
        cv = KFold(n_splits=n_splits, random_state=global_random_seed, shuffle=True)

    # Compute the expected values using our reference Python implementation of
    # target encoding:
    expected_X_fit_transform = np.empty_like(X_train_int_array, dtype=np.float64)

    for train_idx, test_idx in cv.split(X_train_int_array, y_train):
        X_, y_ = X_train_int_array[train_idx, 0], y_numeric[train_idx]
        cur_encodings = _encode_target(X_, y_, n_categories, smooth)
        expected_X_fit_transform[test_idx, 0] = cur_encodings[
            X_train_int_array[test_idx, 0]
        ]

    # Check that we can obtain the same encodings by calling `fit_transform` on
    # the estimator with the same CV parameters:
    target_encoder = TargetEncoder(
        smooth=smooth,
        categories=categories,
        cv=cv,
    )

    X_fit_transform = target_encoder.fit_transform(X_train, y_train)

    assert target_encoder.target_type_ == target_type
    assert_allclose(X_fit_transform, expected_X_fit_transform)
    assert len(target_encoder.encodings_) == 1
    if target_type == "binary":
        assert_array_equal(target_encoder.classes_, target_names)
    else:
        assert target_encoder.classes_ is None

    # compute encodings for all data to validate `transform`
    y_mean = np.mean(y_numeric)
    expected_encodings = _encode_target(
        X_train_int_array[:, 0], y_numeric, n_categories, smooth
    )
    assert_allclose(target_encoder.encodings_[0], expected_encodings)
    assert target_encoder.target_mean_ == pytest.approx(y_mean)

    # Transform on test data, the last value is unknown so it is encoded as the target
    # mean
    expected_X_test_transform = np.concatenate(
        (expected_encodings, np.array([y_mean]))
    ).reshape(-1, 1)

    X_test_transform = target_encoder.transform(X_test)
    assert_allclose(X_test_transform, expected_X_test_transform)