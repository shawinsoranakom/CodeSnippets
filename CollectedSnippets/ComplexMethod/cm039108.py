def test_standard_scaler_constant_features(
    scaler, add_sample_weight, sparse_container, dtype, constant
):
    scaler = clone(scaler)  # Avoid side effects from previous tests.
    if isinstance(scaler, RobustScaler) and add_sample_weight:
        pytest.skip(f"{scaler.__class__.__name__} does not yet support sample_weight")

    rng = np.random.RandomState(0)
    n_samples = 100
    n_features = 1
    if add_sample_weight:
        fit_params = dict(sample_weight=rng.uniform(size=n_samples) * 2)
    else:
        fit_params = {}
    X_array = np.full(shape=(n_samples, n_features), fill_value=constant, dtype=dtype)
    X = X_array if sparse_container is None else sparse_container(X_array)
    X_scaled = scaler.fit(X, **fit_params).transform(X)

    if isinstance(scaler, StandardScaler):
        # The variance info should be close to zero for constant features.
        assert_allclose(scaler.var_, np.zeros(X.shape[1]), atol=1e-7)

    # Constant features should not be scaled (scale of 1.):
    assert_allclose(scaler.scale_, np.ones(X.shape[1]))

    assert X_scaled is not X  # make sure we make a copy
    assert_allclose_dense_sparse(X_scaled, X)

    if isinstance(scaler, StandardScaler) and not add_sample_weight:
        # Also check consistency with the standard scale function.
        X_scaled_2 = scale(X, with_mean=scaler.with_mean)
        assert X_scaled_2 is not X  # make sure we did a copy
        assert_allclose_dense_sparse(X_scaled_2, X)