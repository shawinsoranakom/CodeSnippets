def test_ridge_shapes_type():
    # Test shape of coef_ and intercept_
    rng = np.random.RandomState(0)
    n_samples, n_features = 5, 10
    X = rng.randn(n_samples, n_features)
    y = rng.randn(n_samples)
    Y1 = y[:, np.newaxis]
    Y = np.c_[y, 1 + y]

    ridge = Ridge()

    ridge.fit(X, y)
    assert ridge.coef_.shape == (n_features,)
    assert ridge.intercept_.shape == ()
    assert isinstance(ridge.coef_, np.ndarray)
    assert isinstance(ridge.intercept_, float)

    ridge.fit(X, Y1)
    assert ridge.coef_.shape == (n_features,)
    assert ridge.intercept_.shape == (1,)
    assert isinstance(ridge.coef_, np.ndarray)
    assert isinstance(ridge.intercept_, np.ndarray)

    ridge.fit(X, Y)
    assert ridge.coef_.shape == (2, n_features)
    assert ridge.intercept_.shape == (2,)
    assert isinstance(ridge.coef_, np.ndarray)
    assert isinstance(ridge.intercept_, np.ndarray)