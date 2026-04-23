def test_count_nonzero(csc_container, csr_container):
    X = np.array(
        [[0, 3, 0], [2, -1, 0], [0, 0, 0], [9, 8, 7], [4, 0, 5]], dtype=np.float64
    )
    X_csr = csr_container(X)
    X_csc = csc_container(X)
    X_nonzero = X != 0
    sample_weight = [0.5, 0.2, 0.3, 0.1, 0.1]
    X_nonzero_weighted = X_nonzero * np.array(sample_weight)[:, None]

    for axis in [0, 1, -1, -2, None]:
        assert_array_almost_equal(
            count_nonzero(X_csr, axis=axis), X_nonzero.sum(axis=axis)
        )
        assert_array_almost_equal(
            count_nonzero(X_csr, axis=axis, sample_weight=sample_weight),
            X_nonzero_weighted.sum(axis=axis),
        )

    with pytest.raises(TypeError):
        count_nonzero(X_csc)
    with pytest.raises(ValueError):
        count_nonzero(X_csr, axis=2)

    assert count_nonzero(X_csr, axis=0).dtype == count_nonzero(X_csr, axis=1).dtype
    assert (
        count_nonzero(X_csr, axis=0, sample_weight=sample_weight).dtype
        == count_nonzero(X_csr, axis=1, sample_weight=sample_weight).dtype
    )

    # Check dtypes with large sparse matrices too
    # XXX: test fails on 32bit (Windows/Linux)
    try:
        X_csr.indices = X_csr.indices.astype(np.int64)
        X_csr.indptr = X_csr.indptr.astype(np.int64)
        assert count_nonzero(X_csr, axis=0).dtype == count_nonzero(X_csr, axis=1).dtype
        assert (
            count_nonzero(X_csr, axis=0, sample_weight=sample_weight).dtype
            == count_nonzero(X_csr, axis=1, sample_weight=sample_weight).dtype
        )
    except TypeError as e:
        assert "according to the rule 'safe'" in e.args[0] and np.intp().nbytes < 8, e