def test_pairwise_distances_for_sparse_data(
    coo_container, csc_container, bsr_container, csr_container, global_dtype
):
    # Test the pairwise_distance helper function.
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4)).astype(global_dtype, copy=False)
    Y = rng.random_sample((2, 4)).astype(global_dtype, copy=False)

    # Test with sparse X and Y,
    # currently only supported for Euclidean, L1 and cosine.
    X_sparse = csr_container(X)
    Y_sparse = csr_container(Y)

    S = pairwise_distances(X_sparse, Y_sparse, metric="euclidean")
    S2 = euclidean_distances(X_sparse, Y_sparse)
    assert_allclose(S, S2)
    assert S.dtype == S2.dtype == global_dtype

    S = pairwise_distances(X_sparse, Y_sparse, metric="cosine")
    S2 = cosine_distances(X_sparse, Y_sparse)
    assert_allclose(S, S2)
    assert S.dtype == S2.dtype == global_dtype

    S = pairwise_distances(X_sparse, csc_container(Y), metric="manhattan")
    S2 = manhattan_distances(bsr_container(X), coo_container(Y))
    assert_allclose(S, S2)
    if global_dtype == np.float64:
        assert S.dtype == S2.dtype == global_dtype
    else:
        # TODO Fix manhattan_distances to preserve dtype.
        # currently pairwise_distances uses manhattan_distances but converts the result
        # back to the input dtype
        with pytest.raises(AssertionError):
            assert S.dtype == S2.dtype == global_dtype

    S2 = manhattan_distances(X, Y)
    assert_allclose(S, S2)
    if global_dtype == np.float64:
        assert S.dtype == S2.dtype == global_dtype
    else:
        # TODO Fix manhattan_distances to preserve dtype.
        # currently pairwise_distances uses manhattan_distances but converts the result
        # back to the input dtype
        with pytest.raises(AssertionError):
            assert S.dtype == S2.dtype == global_dtype

    # Test with scipy.spatial.distance metric, with a kwd
    kwds = {"p": 2.0}
    S = pairwise_distances(X, Y, metric="minkowski", **kwds)
    S2 = pairwise_distances(X, Y, metric=minkowski, **kwds)
    assert_allclose(S, S2)

    # same with Y = None
    kwds = {"p": 2.0}
    S = pairwise_distances(X, metric="minkowski", **kwds)
    S2 = pairwise_distances(X, metric=minkowski, **kwds)
    assert_allclose(S, S2)

    # Test that scipy distance metrics throw an error if sparse matrix given
    with pytest.raises(TypeError):
        pairwise_distances(X_sparse, metric="minkowski")
    with pytest.raises(TypeError):
        pairwise_distances(X, Y_sparse, metric="minkowski")