def test_isotonic_thresholds(increasing):
    rng = np.random.RandomState(42)
    n_samples = 30
    X = rng.normal(size=n_samples)
    y = rng.normal(size=n_samples)
    ireg = IsotonicRegression(increasing=increasing).fit(X, y)
    X_thresholds, y_thresholds = ireg.X_thresholds_, ireg.y_thresholds_
    assert X_thresholds.shape == y_thresholds.shape

    # Input thresholds are a strict subset of the training set (unless
    # the data is already strictly monotonic which is not the case with
    # this random data)
    assert X_thresholds.shape[0] < X.shape[0]
    assert np.isin(X_thresholds, X).all()

    # Output thresholds lie in the range of the training set:
    assert y_thresholds.max() <= y.max()
    assert y_thresholds.min() >= y.min()

    assert all(np.diff(X_thresholds) > 0)
    if increasing:
        assert all(np.diff(y_thresholds) >= 0)
    else:
        assert all(np.diff(y_thresholds) <= 0)