def test_inplace_normalize(csr_container, inplace_csr_row_normalize):
    if issubclass(sp.csr_matrix, csr_container):
        ones = np.ones((10, 1))
    else:
        ones = np.ones(10)
    rs = RandomState(10)

    for dtype in (np.float64, np.float32):
        X = rs.randn(10, 5).astype(dtype)
        X_csr = csr_container(X)
        for index_dtype in [np.int32, np.int64]:
            # csr_matrix will use int32 indices by default,
            # up-casting those to int64 when necessary
            if index_dtype is np.int64:
                X_csr.indptr = X_csr.indptr.astype(index_dtype)
                X_csr.indices = X_csr.indices.astype(index_dtype)
            assert X_csr.indices.dtype == index_dtype
            assert X_csr.indptr.dtype == index_dtype
            inplace_csr_row_normalize(X_csr)
            assert X_csr.dtype == dtype
            if inplace_csr_row_normalize is inplace_csr_row_normalize_l2:
                X_csr.data **= 2
            assert_array_almost_equal(np.abs(X_csr).sum(axis=1), ones)