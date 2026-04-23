def test_robust_scaler_attributes(X, with_centering, with_scaling):
    # check consistent type of attributes
    if with_centering and sparse.issparse(X):
        pytest.skip("RobustScaler cannot center sparse matrix")

    scaler = RobustScaler(with_centering=with_centering, with_scaling=with_scaling)
    scaler.fit(X)

    if with_centering:
        assert isinstance(scaler.center_, np.ndarray)
    else:
        assert scaler.center_ is None
    if with_scaling:
        assert isinstance(scaler.scale_, np.ndarray)
    else:
        assert scaler.scale_ is None