def test_min_max_scaler_1d():
    # Test scaling of dataset along single axis
    for X in [X_1row, X_1col, X_list_1row, X_list_1row]:
        scaler = MinMaxScaler(copy=True)
        X_scaled = scaler.fit(X).transform(X)

        if isinstance(X, list):
            X = np.array(X)  # cast only after scaling done

        if _check_dim_1axis(X) == 1:
            assert_array_almost_equal(X_scaled.min(axis=0), np.zeros(n_features))
            assert_array_almost_equal(X_scaled.max(axis=0), np.zeros(n_features))
        else:
            assert_array_almost_equal(X_scaled.min(axis=0), 0.0)
            assert_array_almost_equal(X_scaled.max(axis=0), 1.0)
        assert scaler.n_samples_seen_ == X.shape[0]

        # check inverse transform
        X_scaled_back = scaler.inverse_transform(X_scaled)
        assert_array_almost_equal(X_scaled_back, X)

    # Constant feature
    X = np.ones((5, 1))
    scaler = MinMaxScaler()
    X_scaled = scaler.fit(X).transform(X)
    assert X_scaled.min() >= 0.0
    assert X_scaled.max() <= 1.0
    assert scaler.n_samples_seen_ == X.shape[0]

    # Function interface
    X_1d = X_1row.ravel()
    min_ = X_1d.min()
    max_ = X_1d.max()
    assert_array_almost_equal(
        (X_1d - min_) / (max_ - min_), minmax_scale(X_1d, copy=True)
    )