def test_dtype_preprocess_data(rescale_with_sw, fit_intercept, global_random_seed):
    rng = np.random.RandomState(global_random_seed)
    n_samples = 200
    n_features = 2
    X = rng.rand(n_samples, n_features)
    y = rng.rand(n_samples)
    sw = rng.rand(n_samples) + 1

    X_32 = np.asarray(X, dtype=np.float32)
    y_32 = np.asarray(y, dtype=np.float32)
    sw_32 = np.asarray(sw, dtype=np.float32)
    X_64 = np.asarray(X, dtype=np.float64)
    y_64 = np.asarray(y, dtype=np.float64)
    sw_64 = np.asarray(sw, dtype=np.float64)

    Xt_32, yt_32, X_mean_32, y_mean_32, X_scale_32, sqrt_sw_32 = _preprocess_data(
        X_32,
        y_32,
        fit_intercept=fit_intercept,
        sample_weight=sw_32,
        rescale_with_sw=rescale_with_sw,
    )

    Xt_64, yt_64, X_mean_64, y_mean_64, X_scale_64, sqrt_sw_64 = _preprocess_data(
        X_64,
        y_64,
        fit_intercept=fit_intercept,
        sample_weight=sw_64,
        rescale_with_sw=rescale_with_sw,
    )

    Xt_3264, yt_3264, X_mean_3264, y_mean_3264, X_scale_3264, sqrt_sw_3264 = (
        _preprocess_data(
            X_32,
            y_64,
            fit_intercept=fit_intercept,
            sample_weight=sw_32,  # sample_weight must have same dtype as X
            rescale_with_sw=rescale_with_sw,
        )
    )

    Xt_6432, yt_6432, X_mean_6432, y_mean_6432, X_scale_6432, sqrt_sw_6432 = (
        _preprocess_data(
            X_64,
            y_32,
            fit_intercept=fit_intercept,
            sample_weight=sw_64,  # sample_weight must have same dtype as X
            rescale_with_sw=rescale_with_sw,
        )
    )

    assert Xt_32.dtype == np.float32
    assert yt_32.dtype == np.float32
    assert X_mean_32.dtype == np.float32
    assert y_mean_32.dtype == np.float32
    assert X_scale_32.dtype == np.float32
    if rescale_with_sw:
        assert sqrt_sw_32.dtype == np.float32

    assert Xt_64.dtype == np.float64
    assert yt_64.dtype == np.float64
    assert X_mean_64.dtype == np.float64
    assert y_mean_64.dtype == np.float64
    assert X_scale_64.dtype == np.float64
    if rescale_with_sw:
        assert sqrt_sw_64.dtype == np.float64

    assert Xt_3264.dtype == np.float32
    assert yt_3264.dtype == np.float32
    assert X_mean_3264.dtype == np.float32
    assert y_mean_3264.dtype == np.float32
    assert X_scale_3264.dtype == np.float32
    if rescale_with_sw:
        assert sqrt_sw_3264.dtype == np.float32

    assert Xt_6432.dtype == np.float64
    assert yt_6432.dtype == np.float64
    assert X_mean_6432.dtype == np.float64
    assert y_mean_6432.dtype == np.float64
    assert X_scale_3264.dtype == np.float32
    if rescale_with_sw:
        assert sqrt_sw_6432.dtype == np.float64

    assert X_32.dtype == np.float32
    assert y_32.dtype == np.float32
    assert X_64.dtype == np.float64
    assert y_64.dtype == np.float64

    assert_allclose(Xt_32, Xt_64, rtol=1e-3, atol=1e-6)
    assert_allclose(yt_32, yt_64, rtol=1e-3, atol=1e-6)
    assert_allclose(X_mean_32, X_mean_64, rtol=1e-6)
    assert_allclose(y_mean_32, y_mean_64, rtol=1e-6)
    assert_allclose(X_scale_32, X_scale_64)
    if rescale_with_sw:
        assert_allclose(sqrt_sw_32, sqrt_sw_64, rtol=1e-6)