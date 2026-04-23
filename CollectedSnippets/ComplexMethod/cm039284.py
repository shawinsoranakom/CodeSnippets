def test_hashing_vectorizer():
    v = HashingVectorizer()
    X = v.transform(ALL_FOOD_DOCS)
    token_nnz = X.nnz
    assert X.shape == (len(ALL_FOOD_DOCS), v.n_features)
    assert X.dtype == v.dtype

    # By default the hashed values receive a random sign and l2 normalization
    # makes the feature values bounded
    assert np.min(X.data) > -1
    assert np.min(X.data) < 0
    assert np.max(X.data) > 0
    assert np.max(X.data) < 1

    # Check that the rows are normalized (l2 norm)
    for row in X:
        assert_almost_equal(np.linalg.norm(row.data, 2), 1.0)

    # Check vectorization with some non-default parameters
    v = HashingVectorizer(ngram_range=(1, 2), norm="l1")
    X = v.transform(ALL_FOOD_DOCS)
    assert X.shape == (len(ALL_FOOD_DOCS), v.n_features)
    assert X.dtype == v.dtype

    # ngrams generate more non zeros
    ngrams_nnz = X.nnz
    assert ngrams_nnz > token_nnz
    assert ngrams_nnz < 2 * token_nnz

    # makes the feature values bounded
    assert np.min(X.data) > -1
    assert np.max(X.data) < 1

    # Check that the rows are normalized (l1 norm)
    for row in X:
        assert_almost_equal(np.linalg.norm(row.data, 1), 1.0)