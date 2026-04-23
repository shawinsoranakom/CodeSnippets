def test_check_gcv_mode_choice(sparse_container, X_shape, gcv_mode):
    n, p = X_shape
    X, _ = make_regression(n_samples=n, n_features=p)
    sparse_X = sparse_container is not None
    if sparse_X:
        X = sparse_container(X)
    eigen_mode = "gram" if n <= p else "cov"

    if gcv_mode == "svd" and not sparse_X:
        assert _check_gcv_mode(X, gcv_mode) == "svd"
    elif gcv_mode == "svd" and sparse_X:
        # TODO(1.11) should raises ValueError
        expected_msg = "The 'svd' mode is not supported for sparse X"
        with pytest.warns(FutureWarning, match=expected_msg):
            actual_gcv_mode = _check_gcv_mode(X, gcv_mode)
        assert actual_gcv_mode == eigen_mode
    else:
        assert _check_gcv_mode(X, gcv_mode) == eigen_mode