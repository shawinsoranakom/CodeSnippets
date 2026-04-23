def test_randomized_svd_low_rank_all_dtypes(dtype):
    # Check that extmath.randomized_svd is consistent with linalg.svd
    n_samples = 100
    n_features = 500
    rank = 5
    k = 10
    decimal = 5 if dtype == np.float32 else 7
    dtype = np.dtype(dtype)

    # generate a matrix X of approximate effective rank `rank` and no noise
    # component (very structured signal):
    X = make_low_rank_matrix(
        n_samples=n_samples,
        n_features=n_features,
        effective_rank=rank,
        tail_strength=0.0,
        random_state=0,
    ).astype(dtype, copy=False)
    assert X.shape == (n_samples, n_features)

    # compute the singular values of X using the slow exact method
    U, s, Vt = linalg.svd(X, full_matrices=False)

    # Convert the singular values to the specific dtype
    U = U.astype(dtype, copy=False)
    s = s.astype(dtype, copy=False)
    Vt = Vt.astype(dtype, copy=False)

    for normalizer in ["auto", "LU", "QR"]:  # 'none' would not be stable
        # compute the singular values of X using the fast approximate method
        Ua, sa, Va = randomized_svd(
            X, k, power_iteration_normalizer=normalizer, random_state=0
        )

        # If the input dtype is float, then the output dtype is float of the
        # same bit size (f32 is not upcast to f64)
        # But if the input dtype is int, the output dtype is float64
        if dtype.kind == "f":
            assert Ua.dtype == dtype
            assert sa.dtype == dtype
            assert Va.dtype == dtype
        else:
            assert Ua.dtype == np.float64
            assert sa.dtype == np.float64
            assert Va.dtype == np.float64

        assert Ua.shape == (n_samples, k)
        assert sa.shape == (k,)
        assert Va.shape == (k, n_features)

        # ensure that the singular values of both methods are equal up to the
        # real rank of the matrix
        assert_almost_equal(s[:k], sa, decimal=decimal)

        # check the singular vectors too (while not checking the sign)
        assert_almost_equal(
            np.dot(U[:, :k], Vt[:k, :]), np.dot(Ua, Va), decimal=decimal
        )

        # check the sparse matrix representation
        for csr_container in CSR_CONTAINERS:
            X = csr_container(X)

            # compute the singular values of X using the fast approximate method
            Ua, sa, Va = randomized_svd(
                X, k, power_iteration_normalizer=normalizer, random_state=0
            )
            if dtype.kind == "f":
                assert Ua.dtype == dtype
                assert sa.dtype == dtype
                assert Va.dtype == dtype
            else:
                assert Ua.dtype.kind == "f"
                assert sa.dtype.kind == "f"
                assert Va.dtype.kind == "f"

            assert_almost_equal(s[:rank], sa[:rank], decimal=decimal)