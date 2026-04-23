def test_scaler_int(sparse_container):
    # test that scaler converts integer input to floating
    # for both sparse and dense matrices
    rng = np.random.RandomState(42)
    X = rng.randint(20, size=(4, 5))
    X[:, 0] = 0  # first feature is always of zero
    X_sparse = sparse_container(X)

    with warnings.catch_warnings(record=True):
        scaler = StandardScaler(with_mean=False).fit(X)
        X_scaled = scaler.transform(X, copy=True)
    assert not np.any(np.isnan(X_scaled))

    with warnings.catch_warnings(record=True):
        scaler_sparse = StandardScaler(with_mean=False).fit(X_sparse)
        X_sparse_scaled = scaler_sparse.transform(X_sparse, copy=True)
    assert not np.any(np.isnan(X_sparse_scaled.data))

    assert_array_almost_equal(scaler.mean_, scaler_sparse.mean_)
    assert_array_almost_equal(scaler.var_, scaler_sparse.var_)
    assert_array_almost_equal(scaler.scale_, scaler_sparse.scale_)

    assert_array_almost_equal(
        X_scaled.mean(axis=0), [0.0, 1.109, 1.856, 21.0, 1.559], 2
    )
    assert_array_almost_equal(X_scaled.std(axis=0), [0.0, 1.0, 1.0, 1.0, 1.0])

    X_sparse_scaled_mean, X_sparse_scaled_std = mean_variance_axis(
        X_sparse_scaled.astype(float), 0
    )
    assert_array_almost_equal(X_sparse_scaled_mean, X_scaled.mean(axis=0))
    assert_array_almost_equal(X_sparse_scaled_std, X_scaled.std(axis=0))

    # Check that X has not been modified (copy)
    assert X_scaled is not X
    assert X_sparse_scaled is not X_sparse

    X_scaled_back = scaler.inverse_transform(X_scaled)
    assert X_scaled_back is not X
    assert X_scaled_back is not X_scaled
    assert_array_almost_equal(X_scaled_back, X)

    X_sparse_scaled_back = scaler_sparse.inverse_transform(X_sparse_scaled)
    assert X_sparse_scaled_back is not X_sparse
    assert X_sparse_scaled_back is not X_sparse_scaled
    assert_array_almost_equal(X_sparse_scaled_back.toarray(), X)

    if sparse_container in CSR_CONTAINERS:
        null_transform = StandardScaler(with_mean=False, with_std=False, copy=True)
        with warnings.catch_warnings(record=True):
            X_null = null_transform.fit_transform(X_sparse)
        assert_array_equal(X_null.data, X_sparse.data)
        X_orig = null_transform.inverse_transform(X_null)
        assert_array_equal(X_orig.data, X_sparse.data)