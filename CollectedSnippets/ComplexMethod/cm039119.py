def test_csr_polynomial_expansion_index_overflow(
    degree, n_features, interaction_only, include_bias, csr_container
):
    """Tests known edge-cases to the dtype promotion strategy and custom
    Cython code, including a current bug in the upstream
    `scipy.sparse.hstack`.
    """
    data = [1.0]
    # Use int32 indices as much as we can
    indices_dtype = np.int32 if n_features - 1 <= np.iinfo(np.int32).max else np.int64
    row = np.array([0], dtype=indices_dtype)
    col = np.array([n_features - 1], dtype=indices_dtype)

    # First degree index
    expected_indices = [
        n_features - 1 + int(include_bias),
    ]
    # Second degree index
    expected_indices.append(n_features * (n_features + 1) // 2 + expected_indices[0])
    # Third degree index
    expected_indices.append(
        n_features * (n_features + 1) * (n_features + 2) // 6 + expected_indices[1]
    )

    X = csr_container((data, (row, col)))
    pf = PolynomialFeatures(
        interaction_only=interaction_only, include_bias=include_bias, degree=degree
    )

    # Calculate the number of combinations a-priori, and if needed check for
    # the correct ValueError and terminate the test early.
    num_combinations = pf._num_combinations(
        n_features=n_features,
        min_degree=0,
        max_degree=degree,
        interaction_only=pf.interaction_only,
        include_bias=pf.include_bias,
    )
    if num_combinations > np.iinfo(np.intp).max:
        msg = (
            r"The output that would result from the current configuration would have"
            r" \d* features which is too large to be indexed"
        )
        with pytest.raises(ValueError, match=msg):
            pf.fit(X)
        return

    X_trans = pf.fit_transform(X)

    expected_dtype = np.int64 if num_combinations > np.iinfo(np.int32).max else np.int32
    # Terms higher than first degree
    non_bias_terms = 1 + (degree - 1) * int(not interaction_only)
    expected_nnz = int(include_bias) + non_bias_terms
    assert X_trans.dtype == X.dtype
    assert X_trans.shape == (1, pf.n_output_features_)
    assert X_trans.indptr.dtype == X_trans.indices.dtype == expected_dtype
    assert X_trans.nnz == expected_nnz

    if include_bias:
        assert X_trans[0, 0] == pytest.approx(1.0)
    for idx in range(non_bias_terms):
        assert X_trans[0, expected_indices[idx]] == pytest.approx(1.0)

    offset = interaction_only * n_features
    if degree == 3:
        offset *= 1 + n_features
    assert pf.n_output_features_ == expected_indices[degree - 1] + 1 - offset