def test_scaler_2d_arrays():
    # Test scaling of 2d array along first axis
    rng = np.random.RandomState(0)
    n_features = 5
    n_samples = 4
    X = rng.randn(n_samples, n_features)
    X[:, 0] = 0.0  # first feature is always of zero

    scaler = StandardScaler()
    X_scaled = scaler.fit(X).transform(X, copy=True)
    assert not np.any(np.isnan(X_scaled))
    assert scaler.n_samples_seen_ == n_samples

    assert_array_almost_equal(X_scaled.mean(axis=0), n_features * [0.0])
    assert_array_almost_equal(X_scaled.std(axis=0), [0.0, 1.0, 1.0, 1.0, 1.0])
    # Check that X has been copied
    assert X_scaled is not X

    # check inverse transform
    X_scaled_back = scaler.inverse_transform(X_scaled)
    assert X_scaled_back is not X
    assert X_scaled_back is not X_scaled
    assert_array_almost_equal(X_scaled_back, X)

    X_scaled = scale(X, axis=1, with_std=False)
    assert not np.any(np.isnan(X_scaled))
    assert_array_almost_equal(X_scaled.mean(axis=1), n_samples * [0.0])
    X_scaled = scale(X, axis=1, with_std=True)
    assert not np.any(np.isnan(X_scaled))
    assert_array_almost_equal(X_scaled.mean(axis=1), n_samples * [0.0])
    assert_array_almost_equal(X_scaled.std(axis=1), n_samples * [1.0])
    # Check that the data hasn't been modified
    assert X_scaled is not X

    X_scaled = scaler.fit(X).transform(X, copy=False)
    assert not np.any(np.isnan(X_scaled))
    assert_array_almost_equal(X_scaled.mean(axis=0), n_features * [0.0])
    assert_array_almost_equal(X_scaled.std(axis=0), [0.0, 1.0, 1.0, 1.0, 1.0])
    # Check that X has not been copied
    assert X_scaled is X

    X = rng.randn(4, 5)
    X[:, 0] = 1.0  # first feature is a constant, non zero feature
    scaler = StandardScaler()
    X_scaled = scaler.fit(X).transform(X, copy=True)
    assert not np.any(np.isnan(X_scaled))
    assert_array_almost_equal(X_scaled.mean(axis=0), n_features * [0.0])
    assert_array_almost_equal(X_scaled.std(axis=0), [0.0, 1.0, 1.0, 1.0, 1.0])
    # Check that X has not been copied
    assert X_scaled is not X