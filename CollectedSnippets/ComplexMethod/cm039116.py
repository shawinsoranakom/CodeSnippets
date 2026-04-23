def test_normalize(csr_container):
    # Test normalize function
    # Only tests functionality not used by the tests for Normalizer.
    X = np.random.RandomState(37).randn(3, 2)
    assert_array_equal(normalize(X, copy=False), normalize(X.T, axis=0, copy=False).T)

    rs = np.random.RandomState(0)
    X_dense = rs.randn(10, 5)
    X_sparse = csr_container(X_dense)
    ones = np.ones((10))
    for X in (X_dense, X_sparse):
        for dtype in (np.float32, np.float64):
            for norm in ("l1", "l2"):
                X = X.astype(dtype)
                X_norm = normalize(X, norm=norm)
                assert X_norm.dtype == dtype

                X_norm = toarray(X_norm)
                if norm == "l1":
                    row_sums = np.abs(X_norm).sum(axis=1)
                else:
                    X_norm_squared = X_norm**2
                    row_sums = X_norm_squared.sum(axis=1)

                assert_array_almost_equal(row_sums, ones)

    # Test return_norm
    X_dense = np.array([[3.0, 0, 4.0], [1.0, 0.0, 0.0], [2.0, 3.0, 0.0]])
    for norm in ("l1", "l2", "max"):
        _, norms = normalize(X_dense, norm=norm, return_norm=True)
        if norm == "l1":
            assert_array_almost_equal(norms, np.array([7.0, 1.0, 5.0]))
        elif norm == "l2":
            assert_array_almost_equal(norms, np.array([5.0, 1.0, 3.60555127]))
        else:
            assert_array_almost_equal(norms, np.array([4.0, 1.0, 3.0]))

    X_sparse = csr_container(X_dense)
    for norm in ("l1", "l2"):
        with pytest.raises(NotImplementedError):
            normalize(X_sparse, norm=norm, return_norm=True)
    _, norms = normalize(X_sparse, norm="max", return_norm=True)
    assert_array_almost_equal(norms, np.array([4.0, 1.0, 3.0]))