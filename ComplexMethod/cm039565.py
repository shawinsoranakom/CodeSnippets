def test_pairwise_distances_reduction_is_usable_for(csr_container):
    rng = np.random.RandomState(0)
    X = rng.rand(100, 10)
    Y = rng.rand(100, 10)
    X_csr = csr_container(X)
    Y_csr = csr_container(Y)
    metric = "manhattan"

    # Must be usable for all possible pair of {dense, sparse} datasets
    assert BaseDistancesReductionDispatcher.is_usable_for(X, Y, metric)
    assert BaseDistancesReductionDispatcher.is_usable_for(X_csr, Y_csr, metric)
    assert BaseDistancesReductionDispatcher.is_usable_for(X_csr, Y, metric)
    assert BaseDistancesReductionDispatcher.is_usable_for(X, Y_csr, metric)

    assert BaseDistancesReductionDispatcher.is_usable_for(
        X.astype(np.float64), Y.astype(np.float64), metric
    )

    assert BaseDistancesReductionDispatcher.is_usable_for(
        X.astype(np.float32), Y.astype(np.float32), metric
    )

    assert not BaseDistancesReductionDispatcher.is_usable_for(
        X.astype(np.int64), Y.astype(np.int64), metric
    )

    assert not BaseDistancesReductionDispatcher.is_usable_for(X, Y, metric="pyfunc")
    assert not BaseDistancesReductionDispatcher.is_usable_for(
        X.astype(np.float32), Y, metric
    )
    assert not BaseDistancesReductionDispatcher.is_usable_for(
        X, Y.astype(np.int32), metric
    )

    # F-ordered arrays are not supported
    assert not BaseDistancesReductionDispatcher.is_usable_for(
        np.asfortranarray(X), Y, metric
    )

    assert BaseDistancesReductionDispatcher.is_usable_for(X_csr, Y, metric="euclidean")
    assert BaseDistancesReductionDispatcher.is_usable_for(
        X, Y_csr, metric="sqeuclidean"
    )

    # FIXME: the current Cython implementation is too slow for a large number of
    # features. We temporarily disable it to fallback on SciPy's implementation.
    # See: https://github.com/scikit-learn/scikit-learn/issues/28191
    assert not BaseDistancesReductionDispatcher.is_usable_for(
        X_csr, Y_csr, metric="sqeuclidean"
    )
    assert not BaseDistancesReductionDispatcher.is_usable_for(
        X_csr, Y_csr, metric="euclidean"
    )

    # CSR matrices without non-zeros elements aren't currently supported
    # TODO: support CSR matrices without non-zeros elements
    X_csr_0_nnz = csr_container(X * 0)
    assert not BaseDistancesReductionDispatcher.is_usable_for(X_csr_0_nnz, Y, metric)

    # CSR matrices with int64 indices and indptr (e.g. large nnz, or large n_features)
    # aren't supported as of now.
    # See: https://github.com/scikit-learn/scikit-learn/issues/23653
    # TODO: support CSR matrices with int64 indices and indptr
    X_csr_int64 = csr_container(X)
    X_csr_int64.indices = X_csr_int64.indices.astype(np.int64)
    assert not BaseDistancesReductionDispatcher.is_usable_for(X_csr_int64, Y, metric)