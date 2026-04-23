def test_as_float_array():
    # Test function for as_float_array
    X = np.ones((3, 10), dtype=np.int32)
    X = X + np.arange(10, dtype=np.int32)
    X2 = as_float_array(X, copy=False)
    assert X2.dtype == np.float32
    # Another test
    X = X.astype(np.int64)
    X2 = as_float_array(X, copy=True)
    # Checking that the array wasn't overwritten
    assert as_float_array(X, copy=False) is not X
    assert X2.dtype == np.float64
    # Test int dtypes <= 32bit
    tested_dtypes = [bool, np.int8, np.int16, np.int32, np.uint8, np.uint16, np.uint32]
    for dtype in tested_dtypes:
        X = X.astype(dtype)
        X2 = as_float_array(X)
        assert X2.dtype == np.float32

    # Test object dtype
    X = X.astype(object)
    X2 = as_float_array(X, copy=True)
    assert X2.dtype == np.float64

    # Here, X is of the right type, it shouldn't be modified
    X = np.ones((3, 2), dtype=np.float32)
    assert as_float_array(X, copy=False) is X
    # Test that if X is fortran ordered it stays
    X = np.asfortranarray(X)
    assert np.isfortran(as_float_array(X, copy=True))

    # Test the copy parameter with some matrices
    matrices = [
        sp.csc_matrix(np.arange(5)).toarray(),
        sp.csc_array([np.arange(5)]).toarray(),
        _sparse_random_matrix(10, 10, density=0.10).toarray(),
    ]
    for M in matrices:
        N = as_float_array(M, copy=True)
        N[0, 0] = np.nan
        assert not np.isnan(M).any()