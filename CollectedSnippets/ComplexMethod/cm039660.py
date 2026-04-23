def test_regressor_partial_fit(csr_container, average):
    y_bin = y.copy()
    y_bin[y != 1] = -1

    data = csr_container(X) if csr_container is not None else X
    reg = PassiveAggressiveRegressor(random_state=0, average=average, max_iter=100)
    for t in range(50):
        reg.partial_fit(data, y_bin)
    pred = reg.predict(data)
    assert np.mean((pred - y_bin) ** 2) < 1.7
    if average:
        assert hasattr(reg, "_average_coef")
        assert hasattr(reg, "_average_intercept")
        assert hasattr(reg, "_standard_intercept")
        assert hasattr(reg, "_standard_coef")