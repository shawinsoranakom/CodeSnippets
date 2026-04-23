def test_tfidf_transformer_copy(csr_container):
    """Check the behaviour of TfidfTransformer.transform with the copy parameter."""
    X = sparse.rand(10, 20000, dtype=np.float64, random_state=42)
    X_csr = csr_container(X)

    # keep a copy of the original matrix for later comparison
    X_csr_original = X_csr.copy()

    transformer = TfidfTransformer().fit(X_csr)

    X_transform = transformer.transform(X_csr, copy=True)
    assert_allclose_dense_sparse(X_csr, X_csr_original)
    assert X_transform is not X_csr

    X_transform = transformer.transform(X_csr, copy=False)
    # allow for config["sparse_interface"] to change output type
    # there should be no data copied, but the `id` will change.
    if _align_api_if_sparse(X_csr) is X_csr:
        assert X_transform is X_csr
    else:
        assert X_transform is not X_csr
        assert X_transform.indptr is X_csr.indptr
        assert X_transform.indices.base is X_csr.indices.base
        assert X_transform.data.base is X_csr.data.base

    with pytest.raises(AssertionError):
        assert_allclose_dense_sparse(X_csr, X_csr_original)