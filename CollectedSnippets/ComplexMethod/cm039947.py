def test_ordering():
    # Check that ordering is enforced correctly by validation utilities.
    # We need to check each validation utility, because a 'copy' without
    # 'order=K' will kill the ordering.
    X = np.ones((10, 5))
    for A in X, X.T:
        for copy in (True, False):
            B = check_array(A, order="C", copy=copy)
            assert B.flags["C_CONTIGUOUS"]
            B = check_array(A, order="F", copy=copy)
            assert B.flags["F_CONTIGUOUS"]
            if copy:
                assert A is not B

    X = sp.csr_array(X)
    X.data = X.data[::-1]
    assert not X.data.flags["C_CONTIGUOUS"]