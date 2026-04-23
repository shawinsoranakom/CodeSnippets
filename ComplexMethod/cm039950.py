def test_check_array_dtype_warning():
    X_int_list = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    X_float32 = np.asarray(X_int_list, dtype=np.float32)
    X_int64 = np.asarray(X_int_list, dtype=np.int64)
    X_csr_float32 = sp.csr_array(X_float32)
    X_csc_float32 = sp.csc_array(X_float32)
    X_csc_int32 = sp.csc_array(X_int64, dtype=np.int32)
    integer_data = [X_int64, X_csc_int32]
    float32_data = [X_float32, X_csr_float32, X_csc_float32]
    with warnings.catch_warnings():
        warnings.simplefilter("error")

        for X in integer_data:
            X_checked = check_array(X, dtype=np.float64, accept_sparse=True)
            assert X_checked.dtype == np.float64

        for X in float32_data:
            X_checked = check_array(
                X, dtype=[np.float64, np.float32], accept_sparse=True
            )
            assert X_checked.dtype == np.float32
            assert X_checked is X

            X_checked = check_array(
                X,
                dtype=[np.float64, np.float32],
                accept_sparse=["csr", "dok"],
                copy=True,
            )
            assert X_checked.dtype == np.float32
            assert X_checked is not X

        X_checked = check_array(
            X_csc_float32,
            dtype=[np.float64, np.float32],
            accept_sparse=["csr", "dok"],
            copy=False,
        )
        assert X_checked.dtype == np.float32
        assert X_checked is not X_csc_float32
        assert X_checked.format == "csr"