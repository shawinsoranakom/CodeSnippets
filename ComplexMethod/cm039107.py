def test_standard_scaler_dtype(add_sample_weight, sparse_container):
    # Ensure scaling does not affect dtype
    rng = np.random.RandomState(0)
    n_samples = 10
    n_features = 3
    if add_sample_weight:
        sample_weight = np.ones(n_samples)
    else:
        sample_weight = None
    with_mean = True
    if sparse_container is not None:
        # scipy sparse containers do not support float16, see
        # https://github.com/scipy/scipy/issues/7408 for more details.
        supported_dtype = [np.float64, np.float32]
    else:
        supported_dtype = [np.float64, np.float32, np.float16]
    for dtype in supported_dtype:
        X = rng.randn(n_samples, n_features).astype(dtype)
        if sparse_container is not None:
            X = sparse_container(X)
            with_mean = False

        scaler = StandardScaler(with_mean=with_mean)
        X_scaled = scaler.fit(X, sample_weight=sample_weight).transform(X)
        assert X.dtype == X_scaled.dtype
        assert scaler.mean_.dtype == np.float64
        assert scaler.scale_.dtype == np.float64